from interfaces import Actor
from event import notify, Event

def factory(name, settings):
    return DummyActor(name)

class DummyActor(Actor):
    def __init__(self, name):
        self.name = name
        self.power = 0

    def on(self):
        self.updatePower(100.0)
    def off(self):
        self.updatePower(0.0)

    def updatePower(self, power):
        self.power = power
        notify(Event(source=self.name, endpoint='power', data=self.power))
        print("%s: Setting power to %f"%(self.name, self.power))

    def callback(self, endpoint, data):
        if endpoint == 'state':
            if data == 0:
                print("Turning %s off"%self.name)
                self.off()
            elif data == 1:
                print("Turning %s on"%self.name)
                self.on()
            else:
                print("Warning: DummyActor:%s unsupported data value: %d"%(self.name, data))
