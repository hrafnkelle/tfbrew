import asyncio
import logging
from collections import deque
from time import time

from aiohttp import web
import json
import sockjs

import interfaces
import event
from common import app, components


logger = logging.getLogger(__name__)


class Controller(interfaces.Component, interfaces.Runnable):
    def __init__(self, name, sensor, actor, logic, agitator=None, targetTemp=0.0, initiallyEnabled=False):
        self.name = name
        self._enabled = initiallyEnabled
        self._autoMode = False
        self.sensor = sensor
        self.actor = actor
        self.agitator = agitator
        self.targetTemp = targetTemp
        self.logic = logic
        self.timestamp_history = deque(maxlen=100)
        self.power_history = deque(maxlen=100)
        self.temp_history = deque(maxlen=100)
        self.setpoint_history = deque(maxlen=100)
        sockjs.add_endpoint(app, prefix='/controllers/%s/ws'%self.name, name='%s-ws'%self.name, handler=self.websocket_handler)

    def callback(self, endpoint, data):
        includeSetpoint = False
        if endpoint in ['state', 'enabled']:
            self.enabled = bool(data)
            self.actor.updatePower(0.0)
            logger.info("Setting %s ctrl enabled to %r"%(self.name, bool(data)))
        elif endpoint == 'automatic':
            self.actor.updatePower(0.0)
            self.automatic = bool(data)
            logger.info("Setting %s ctrl automatic to %r"%(self.name, bool(self._autoMode)))
        elif endpoint == 'setpoint':
            self.setSetpoint(float(data))
            includeSetpoint = True
        elif endpoint == 'power':
            self.actor.updatePower(float(data))
            logger.info("Setting %s ctrl power to %f"%(self.name, float(data)))
        elif endpoint == 'agitating':
            pwr = 100*float(data)
            logger.info("Setting %s ctrl automatic to %r"%(self.name, pwr))
            self.agitator.updatePower(pwr)
        else:
            self.logic.callback(endpoint, data)
            #logger.warning("Unknown type/endpoint for Contorller %s"%endpoint)
        self.broadcastDetails(includeSetpoint)        

    def setSetpoint(self, setpoint):
        self.targetTemp = setpoint
        event.notify(event.Event(source=self.name, endpoint='setpoint', data=self.targetTemp))

    def broadcastDetails(self, includeSetpoint=False):
        manager = sockjs.get_manager('%s-ws'%self.name, app)
        details = self.getDetails()
        if not includeSetpoint:
            details.pop('setpoint', None)
        manager.broadcast(details)


    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, state):
        self._enabled = state
        if not self._enabled:
            self.actor.updatePower(0.0)
        event.notify(event.Event(source=self.name, endpoint='enabled', data=self.enabled))

    @property
    def automatic(self):
        return self._autoMode

    @automatic.setter
    def automatic(self, state):
        self._autoMode = state

    def getDetails(self):
        details = {
            'temperature': self.sensor.temp(),
            'setpoint': self.targetTemp,
            'automatic': self.automatic,
            'name': self.name,
            'power': self.actor.getPower(),
            'agitating': self.agitator.getPower()>0 if self.agitator else None,
            'enabled': self.enabled,
            'wsUrl': '/controllers/%s/ws'%self.name
        }
        return details

    async def run(self):
        await asyncio.sleep(5)
        while True:
            output = self.actor.getPower()
            if self.enabled:
                if self._autoMode:
                    output = self.logic.calc(self.sensor.temp(), self.targetTemp)
                self.actor.updatePower(output)
            self.broadcastDetails()
            self.timestamp_history.append(time())
            self.power_history.append(output)
            self.temp_history.append(self.sensor.temp())
            self.setpoint_history.append(self.targetTemp)
            await asyncio.sleep(10)



    async def websocket_handler(self, manager, session, msg):
        if msg.type == sockjs.MsgType.OPEN:
            self.broadcastDetails()
        if msg.type == sockjs.MsgType.MESSAGE:
            data = json.loads(msg.data)
            for endpoint, value in data.items():
                self.callback(endpoint, value)
        pass


async def listControllers(request):
    res=request.app.router['controllerDetail']
    controllers = {name: {'url': str(request.url.with_path(str(res.url_for(name=name))))} for (name, component) in components.items() if isinstance(component, Controller)}
    return web.json_response(controllers)

async def controllerDetail(request):
    try:
        controllerName = request.match_info['name']
        details = components[controllerName].getDetails()
        return web.json_response(details)
    except KeyError as e:
        raise web.HTTPNotFound(reason='Unknown controller %s'%str(e))

async def dataHistory(request):
    try:
        controllerName = request.match_info['name']
        controller = components[controllerName]
        data = {
            'label': list(controller.timestamp_history),
            'temperature': list(controller.temp_history),
            'power': list(controller.power_history),
            'setpoint': list(controller.setpoint_history)
            }
        return web.json_response(data)
    except KeyError as e:
        raise web.HTTPNotFound(reason='Unknown controller %s'%str(e))


app.router.add_get('/controllers', listControllers)
app.router.add_get('/controllers/{name}', controllerDetail, name='controllerDetail')
app.router.add_get('/controllers/{name}/datahistory', dataHistory, name='dataHistory')
