from interfaces import Sensor
import aiofiles
import asyncio
from aiohttp import web

def factory(name, settings):
    return W1Sensor(name, settings['id'], settings['offset'])

class W1Sensor(Sensor):
    def __init__(self, name, sensorId, offset=0):
        self.name = name
        self.sensorId = sensorId
        self.offset = offset
        self.lastTemp = 0.0
        asyncio.get_event_loop().create_task(self.run())


    async def run(self, app):
        while True:
            self.lastTemp = await self.readTemp() + self.offset
            await asyncio.sleep(2)

    async def readTemp(self):
        async with aiofiles.open('/sys/bus/w1/devices/%s/w1_slave'% self.sensorId, mode='r') as sensor_file:
            contents = await sensor_file.read()
        if contents.split('\n')[0].split(' ')[11] == "YES":
            temp = float(contents.split("=")[-1]) / 1000
            return temp
        else:
            return -100

    def temp(self):
        return self.lastTemp
