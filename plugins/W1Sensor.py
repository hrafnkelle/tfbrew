import aiofiles
import asyncio
from interfaces import Sensor
from event import notify, Event

def factory(name, settings):
    id = settings['id']
    offset = settings.get('offset', 0.0)
    pollInterval = settings.get('pollInterval', 2.0)
    return W1Sensor(name, id, offset, pollInterval)

class W1Sensor(Sensor):
    def __init__(self, name, sensorId, offset=0, pollInterval=0):
        self.name = name
        self.sensorId = sensorId
        self.offset = offset
        self.lastTemp = 0.0
        self.pollInterval = pollInterval
        asyncio.get_event_loop().create_task(self.run())


    async def run(self):
        while True:
            self.lastTemp = await self.readTemp() + self.offset
            notify(Event(source=self.name, endpoint='temperature', data=self.lastTemp))
            await asyncio.sleep(self.pollInterval)

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
