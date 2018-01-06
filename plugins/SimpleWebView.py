import asyncio
import struct
import time
import sys

from aiohttp import web

import interfaces
from event import notify, Event

from common import app

def factory(name, settings):
    print("Initializing SimpleWebView")
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