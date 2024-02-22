# Blynk.py
# 
# Changelog:
#  20-FEB-24: Replaced BlynkLib.py (EOL version Blynk 1.0) with new Blynk.py supporting Blynk IoT aka 2.0.
#             Required install of BlynkLib 1.0.0 from https://github.com/vshymanskyy/blynk-library-python.
#
# Ver: 1.0

import asyncio
import logging
import BlynkLib

import interfaces
from event import notify, Event

logger = logging.getLogger(__name__)

def factory(name, settings):
    blynkServer = settings.get('server','blynk.cloud')
    blynkPort = settings.get('port', 443)
    component = BlynkComponent(name, blynkServer, blynkPort, settings['token'])
    return component

class BlynkComponent(interfaces.Component):
    def __init__(self, name, server, port, token):
        self.name = name
        self.server = server
        self.port = port
        self.token = token
        self.blynk = BlynkLib.Blynk(self.token, server=self.server)
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.blynk_task())

    async def blynk_task(self):
        @self.blynk.on("V*")
        def blynk_handle_vpins(pin, value):
            notify(Event(source=self.name, endpoint='v%d'% int(pin), data=round(float(value[0]), 1)))

        @self.blynk.on("connected")
        def blynk_connected(ping):
            print("Access granted, happy Blynking!")
            print('Blynk ready. Ping:', ping, 'ms')

        while True:
            self.blynk.run()
            await asyncio.sleep(0.1)  # Adjust sleep time as needed

    def callback(self, endpoint, data):
        pin = int(endpoint[1:])
        self.blynk.virtual_write(pin, data)
