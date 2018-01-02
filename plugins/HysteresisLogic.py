import interfaces

def factory(name, settings):
    hysteresisOver = settings.get('allowedOvershoot',0.5)
    hysteresisUnder = settings.get('allowedUndershoot',0.5)
    return HysteresisLogic(hysteresisOver, hysteresisUnder)

class HysteresisLogic(interfaces.Logic):
    def __init__(self, hysteresisUnder=0.5, hysteresisOver=0.5):
        self.hysteresisUnder = hysteresisUnder
        self.hysteresisOver = hysteresisOver
        self.lastOutput = 0
        self.output = 0

    def calc(self, input, setpoint):
        if self.lastOutput == 1:
            if input >= (setpoint - self.hysteresisUnder):
                self.output = 1
            else:
                self.output = 0
        else:
            if input >= (setpoint + self.hysteresisOver):
                self.output = 1
            else:
                self.output = 0

        self.lastOutput = self.output
        return self.output*100.0
