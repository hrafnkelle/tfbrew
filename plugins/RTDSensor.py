import logging
import aiofiles
import asyncio
import math
from time import sleep
import spidev
from event import notify, Event
from interfaces import Sensor

logger = logging.getLogger(__name__)

def factory(name, settings):
    device = settings.get('device', 0)
    bus = settings.get('bus', 0)
    offset = settings.get('offset', 0.0)
    pollInterval = settings.get('pollInterval', 2.0)
    rref = settings.get('referenceResistance', 430)
    r0 = settings.get('zeroDegResistance', 100)
    return RTDSensor(name, bus, device, rref, r0, offset, pollInterval)

class RTDSensor(Sensor):
    def __init__(self, name, bus=0, device=0, rref=430, r0=100, offset=0, pollInterval=0):
        self.name = name
        self.offset = offset
        self.lastTemp = 0.0
        self.pollInterval = pollInterval
        self.device = device
        self.bus = bus
        self.rref = rref
        self.r0 = r0
        self.spi = spidev.SpiDev()
        self.spi.open(self.bus, self.device)
        self.spi.mode = 0b01
        self.spi.max_speed_hz = 500000

    async def run(self):
        while True:
            try:
                self.lastTemp = await asyncio.get_event_loop().run_in_executor(None, self.readTemp) + self.offset
                notify(Event(source=self.name, endpoint='temperature', data=self.lastTemp))
            except RuntimeError as e:
                logger.debug(str(e))
            await asyncio.sleep(self.pollInterval)

    def readTemp(self):
        self.spi.xfer([0x80, 0xB3])
        self.spi.xfer([0x00])
        sleep(0.1)
        data = self.spi.xfer([0,0,0,0,0,0,0,0,0])
        adc_res = (( data[2] << 8 ) | data[3] ) >> 1
        return self.calcTemp(adc_res)

    def calcTemp(self, adc_res):
            a = 3.9083e-3
            b = -5.7750e-7
            rt = (adc_res*self.rref) / 32768.0 # Resistance of RTD 
            temp_C = -a*self.r0 + math.sqrt(self.r0**2*a**2 - 4*self.r0*b*(self.r0-rt))
            temp_C /= 2*self.r0*b
            if (temp_C < 0): 
                temp_C = (adc_res/32) - 256
            return temp_C

    def temp(self):
        return self.lastTemp

if __name__ == '__main__':

    def blip():
        asyncio.get_event_loop().call_later(0.1, blip)

    loop = asyncio.get_event_loop()
    settings = {}
    sensor = factory("RTDSensor", settings)
    loop.call_soon(blip)

    temp = sensor.readTemp()

    try:
        loop.run_forever()
    finally:
        loop.close()

