from functools import partial
import asyncio
import struct
import time
import sys
import logging

from aiohttp import web

import interfaces
from event import notify, Event

from common import app

logger = logging.getLogger(__name__)

def factory(name, settings):
    logger.info("Initializing SimpleWebView")
    return SimpleWebView(name, settings['endpoints'])

class SimpleWebView(interfaces.Component):
    def __init__(self, name, endpoints):
        self.name = name
        self.endpointData = {}
        app.router.add_get('/', self.webView)

        for name in endpoints:
            app.router.add_put("/%s"%name, partial(self.handler, name))

    def callback(self, endpoint, data):
        self.endpointData[endpoint] = data

    async def handler(self, name, request):
        print("handling %s"%name)
        stuff = await request.json()
        print("endpoint %s got %s"%(name, stuff))
        notify(Event(source=self.name, endpoint=name, data=stuff))
        return web.json_response(stuff)

    def webView(self, request):
        return web.json_response(text=str(self.endpointData))