"""
Implements using a TPLink socket as an actor
"""
import asyncio
import logging

from aiohttp import web

from interfaces import Actor
from event import notify, Event

logger = logging.getLogger(__name__)

def factory(name, settings):
    return TPLinkActor(name, settings)

# Encryption and Decryption of TP-Link Smart Home Protocol
# XOR Autokey Cipher with starting key = 171
def encrypt(string):
    key = 171
    result = b'\0\0\0\0'
    for i in string:
        a = key ^ i
        key = a
        result += bytes([a])
    return result

def decrypt(string):
    key = 171
    result = b''
    for i in string:
        a = key ^ i
        key = i
        result += bytes(chr(a), 'ascii')
    return result


class TPLinkProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        #print("connected")

    def connection_lost(self, exc):
        if exc:
            logger.error(exc)

    def data_received(self, data):
        msg = decrypt(data[4:])
        #print(msg.decode('ascii'))

class TPLinkActor(Actor):
    onMsg = '{"system":{"set_relay_state":{"state":1}}}'
    offMsg = '{"system":{"set_relay_state":{"state":0}}}'
    infoMsg = '{"system":{"get_sysinfo":{}}}'
    refreshInterval = 10

    def __init__(self, name, settings):
        self.name = name
        self.power = 0
        self.loop = asyncio.get_event_loop()
        self.protocol = TPLinkProtocol()
        self.settings = settings
        asyncio.ensure_future(self.schedule())

    async def schedule(self):
        while True:
            if self.power == 100.0:
                await self.send(self.onMsg)
                await asyncio.sleep(self.refreshInterval)
            elif self.power == 0.0:
                await self.send(self.offMsg)
                await asyncio.sleep(self.refreshInterval)
            else:
                onTime = self.refreshInterval*self.power/100.0
                offTime = self.refreshInterval - onTime
                await self.send(self.onMsg)
                await asyncio.sleep(onTime)
                await self.send(self.offMsg)
                await asyncio.sleep(offTime)


    def updatePower(self, power):
        self.power = power
        notify(Event(source=self.name, endpoint='power', data=power))

    async def isRelayOn(self):
            await self.send(self.infoMsg)

    async def send(self, msg):
        try:
            (transport, protocol) = await self.loop.create_connection(lambda: self.protocol, self.settings['ip'], 9999)
            transport.write(encrypt(bytes(msg,'ascii')))
        except OSError as e:
            logger.warning("TPLinkActor %s: %s"%(self.name, str(e)))

    def on(self):
        print("Turning %s on"%self.name)
        asyncio.ensure_future(self.send(self.onMsg))
        self.updatePower(100.0)

    def off(self):
        print("Turning %s off"%self.name)
        asyncio.ensure_future(self.send(self.offMsg))
        self.updatePower(0.0)

    def callback(self, endpoint, data):
        if endpoint == 'state':
            if data == 0:
                self.off()
            elif data == 1:
                self.on()
            else:
                logger.warning("TPLinkActor:%s unsupported data value for state endpoint: %d"%(self.name, data))
        elif endpoint == 'power':
            if data == 100.0:
                self.on()
            elif data == 0.0:
                self.off()
            else:
                self.updatePower(data)
        else:
            logger.warning("TPLinkActor: %s unsupported endpoint %s"%(self.name, endpoint))

if __name__ == '__main__':

    def blip():
        asyncio.get_event_loop().call_later(0.1, blip)

    loop = asyncio.get_event_loop()
    settings = {'ip': '192.168.8.116'}
    actor = factory("TPLinkActor", settings)
    loop.call_soon(blip)

    actor.updatePower(15.0)
    #actor.off()

    try:
        loop.run_forever()
    finally:
        loop.close()
