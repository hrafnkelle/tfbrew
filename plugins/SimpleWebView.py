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
    return SimpleWebView(name)

class SimpleWebView(interfaces.Component):
    def __init__(self, name):
        self.name = name
        self.endpointData = {}
        app.router.add_get('/', self.webView)

    def callback(self, endpoint, data):
        self.endpointData[endpoint] = data

    def webView(self, request):
        return web.json_response(text=str(self.endpointData))