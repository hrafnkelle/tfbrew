import asyncio
import logging

import interfaces
import event

logger = logging.getLogger(__name__)

class Controller(interfaces.Component, interfaces.Runnable):
    def __init__(self, name, sensor, actor, logic, targetTemp=0.0, initialState='off'):
        self.name = name
        self.state = initialState
        self.heater_override = 0
        self.sensor = sensor
        self.actor = actor
        self.targetTemp = targetTemp
        self.logic = logic
        asyncio.ensure_future(self.run())

    def callback(self, endpoint, data):
        if endpoint == 'state':
            if data == 0:
                logger.info("Turning %s ctrl off"%self.name)
                self.setState('off')
            elif data == 1:
                logger.info("Turning %s ctrl on"%self.name)
                self.setState('on')
            else:
                logger.warning("Controller unsupported data value: %f"%data)
        elif endpoint == 'setpoint':
            self.setSetpoint(float(data))
        elif endpoint == 'heater_override':
            self.heater_override = int(data)
        else:
            self.logic.callback(endpoint, data)
            #logger.warning("Unknown type/endpoint for Contorller %s"%endpoint)

    def setSetpoint(self, setpoint):
        self.targetTemp = setpoint
        event.notify(event.Event(source=self.name, endpoint='setpoint', data=self.targetTemp))

    def setState(self, state):
        self.state = state
        if self.state == 'off':
            self.actor.updatePower(0.0)
        event.notify(event.Event(source=self.name, endpoint='state', data=self.state))


    async def run(self):
        while True:
            if self.state == 'on':
                output = self.logic.calc(self.sensor.temp(), self.targetTemp)
                if self.heater_override == 1:
                    output = 100
                self.actor.updatePower(output)
                await asyncio.sleep(10)
            else:
                await asyncio.sleep(1)
