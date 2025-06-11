import logging

logger = logging.getLogger(__name__)

class Component:
    def callback(self, endpoint, data):
        logger.debug("Not handled event: %s"%str(data))
        pass

class Runnable:
    async def run(self):
        pass

class Measurable:
    def getMeasurements(self):
        pass

class Sensor(Component, Runnable, Measurable):

    async def run(sel):
        pass

    async def readTemp(self):
        pass

class Actor(Component, Runnable):
    def updatePower(self, power):
        pass

    def getPower(self):
        pass
        
    def on(self):
        pass

    def off(self):
        pass


class Logic(Component):
    def calc(self, input, setpoint):
        pass

class Controller(Component, Runnable):
    pass