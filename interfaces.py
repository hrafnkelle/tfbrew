import logging

logger = logging.getLogger(__name__)

class Component:
    def callback(self, endpoint, data):
        logger.debug("Not handled event: %s"%str(data))
        pass

class Runnable:
    def run(self, app):
        pass

class Measurable:
    def getMeasurements(self):
        pass

class Sensor(Component, Runnable, Measurable):

    async def run(self, app):
        pass

    async def readTemp(self):
        pass

class Actor(Component, Runnable):
    def updatePower(self, power):
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