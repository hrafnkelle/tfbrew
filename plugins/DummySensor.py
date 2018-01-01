"""
Sensor that generates fake data by adding noise to an expected
"""
import asyncio
from random import normalvariate

from interfaces import Sensor

from event import notify, Event

def factory(name, settings):
    return DummySensor(name, settings['fakeTemp'])

class DummySensor(Sensor):
    def __init__(self, name, fakeTemp):
        self.fakeTemp = fakeTemp
        self.lastTemp = 0
        self.name = name
        asyncio.get_event_loop().create_task(self.run())


    async def run(self):
        while True:
            self.lastTemp = await self.readTemp() 
            await asyncio.sleep(10)

    async def readTemp(self):
        await asyncio.sleep(2)
        temp = normalvariate(self.fakeTemp, 0.5)
        notify(Event(source=self.name, endpoint='temperature', data=temp))
        return temp

    def temp(self):
        return self.lastTemp


    # def get(self, request):
    #     return web.Response(text="%f"%self.temp())
