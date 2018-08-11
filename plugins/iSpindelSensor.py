import asyncio
import logging

from aiohttp import web
import json

import interfaces
from common import app
from event import notify, Event

logger = logging.getLogger(__name__)

def factory(name, settings  ):
    return iSpindelSensor(name, settings)

class iSpindelSensor(interfaces.Sensor):
    def __init__(self, name, settings):
        self.name = name
        self.last_temperature = 0
        app.router.add_post('/ispindel/%s'%name, self.post_handler)

    async def run(self):
        while True:
            await asyncio.sleep(10)

    async def readTemp(self):
        self.last_temperature
    
    async def post_handler(self, request):
        try:
            data = await request.json()
            self.last_temperature = data['temperature']
            for key, value in data.items():
                notify(Event(source=self.name, endpoint=key, data=value))
            
            return web.Response(text="Thank you")
        except json.JSONDecodeError as e:
            logger.warning('Malformed JSON received from iSpindel %s: %s'%(self.name, str(e)))
            raise web.HTTPBadRequest(reason='Malformed JSON %s'%str(e))
