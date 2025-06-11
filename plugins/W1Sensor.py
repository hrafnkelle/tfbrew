import logging
import aiofiles
import asyncio
from interfaces import Sensor
from event import notify, Event

logger = logging.getLogger(__name__)

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

    async def run(self):
        while True:
            try:
                self.lastTemp = await self.readTemp() + self.offset
                notify(Event(source=self.name, endpoint='temperature', data=self.lastTemp))
            except RuntimeError as e:
                logger.debug(str(e))
            await asyncio.sleep(self.pollInterval)

    async def readTemp(self):
        # Read the sensor file and robustly parse the temperature
        try:
            async with aiofiles.open(f'/sys/bus/w1/devices/{self.sensorId}/w1_slave', mode='r') as sensor_file:
                contents = await sensor_file.read()
        except FileNotFoundError:
            raise RuntimeError(f"Sensor file not found for {self.sensorId}")
        if not contents:
            raise RuntimeError(f"Sensor file for {self.sensorId} is empty")
        lines = contents.strip().split('\n')
        if len(lines) < 2:
            raise RuntimeError(f"Unexpected sensor file format: {contents}")
        if "YES" not in lines[0]:
            raise RuntimeError(f"Failed to read W1 Temperature: {contents}")
        # Find 't=' in the second line
        temp_str = None
        if 't=' in lines[1]:
            temp_str = lines[1].split('t=')[-1]
        elif '=' in lines[1]:
            temp_str = lines[1].split('=')[-1]
        if temp_str is None or not temp_str.strip().lstrip('-').isdigit():
            raise RuntimeError(f"Temperature value not found in: {contents}")
        temp = float(temp_str) / 1000
        return temp

    def temp(self):
        return self.lastTemp
