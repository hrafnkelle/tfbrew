import asyncio

import interfaces
import event

class Controller(interfaces.Component, interfaces.Runnable):
    def __init__(self, name, sensor, actor, logic, targetTemp=0.0, initialState='off'):
        self.name = name
        self.state = initialState
        self.sensor = sensor
        self.actor = actor
        self.targetTemp = targetTemp
        self.logic = logic
        asyncio.ensure_future(self.run())

    def callback(self, endpoint, data):
        if endpoint == 'state':
            if data == 0:
                print("Turning %s ctrl off"%self.name)
                self.setState('off')
            elif data == 1:
                print("Turning %s ctrl on"%self.name)
                self.setState('on')
            else:
                print("Warning: Controller unsupported data value: %f"%data)
        elif endpoint == 'setpoint':
            self.setSetpoint(float(data))
        else:
            print("Warning: Unknown type/endpoint for Contorller %s"%endpoint)

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
                self.actor.updatePower(output)
                await asyncio.sleep(10)
            else:
                self.actor.updatePower(0)
                await asyncio.sleep(1)
