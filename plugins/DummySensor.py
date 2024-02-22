# DummySensor.py
# 
# Changelog:
#  22-FEB-24: Updated temp to use 2.5 standard deviations and round to 1st decimal
#               to make temp changes more noticable during testing.
#
# Ver: 1.0

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
        temp = round(normalvariate(self.fakeTemp, 2.5), 1)
        notify(Event(source=self.name, endpoint='temperature', data=temp))
        return temp

    def temp(self):
        return self.lastTemp

    def callback(self, endpoint, data):
        if endpoint == 'temperature':
            self.fakeTemp = float(data)
        else:
            super.callback(endpoint, data)

    # def get(self, request):
    #     return web.Response(text="%f"%self.temp())
