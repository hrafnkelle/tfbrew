"""
TFBrew extension for logging to the Ubidots IoT cloud
"""
import asyncio
import logging
import json
import aiohttp

import interfaces

logger = logging.getLogger(__name__)

def factory(name, settings):
    return UbidotsLogger(name, settings['token'], settings['variables'])   

class UbidotsLogger(interfaces.Component):
    def __init__(self, name, ubidotsToken, variables):
        self.name = name
        self.session = aiohttp.ClientSession()
        self.headers = {'X-Auth-Token': ubidotsToken, 'Content-Type': 'application/json'}
        self.variables = variables
        self.loop = asyncio.get_event_loop()

    def prepareVariables(self, variableNames):
        for name, token in variableNames.items():
            self.variables[name] = self.api.get_variable(token)

    async def postToUbidots(self, endpoint, data):
        response = await self.session.post('http://things.ubidots.com/api/v1.6/variables/%s/values'%self.variables[endpoint],
                            data=json.dumps({'value': data}), headers=self.headers)
        

    def callback(self, endpoint, data):
        asyncio.ensure_future(self.postToUbidots(endpoint, data))

