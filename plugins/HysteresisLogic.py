import interfaces

def factory(name, settings):
    hysteresisOver = settings.get('allowedOvershoot', 0.5)
    hysteresisUnder = settings.get('allowedUndershoot', 0.5)
    return HysteresisLogic(hysteresisOver, hysteresisUnder)

class HysteresisLogic(interfaces.Logic):
    def __init__(self, hysteresisUnder=0.5, hysteresisOver=0.5):
        self.hysteresisUnder = hysteresisUnder
        self.hysteresisOver = hysteresisOver
        self.lastOutput = 0
        self.output = 0

    def shouldCool(self, currentTemp, threshold):
        if currentTemp >= threshold:
            return 1
        else:
            return 0


    def calc(self, input, setpoint):
        if self.lastOutput == 1:
            self.output = self.shouldCool(input, setpoint - self.hysteresisUnder)
        else:
            self.output = self.shouldCool(input, setpoint + self.hysteresisOver)

        self.lastOutput = self.output
        return self.output*100.0

    def callback(self, endpoint, data):
        if endpoint == 'undershoot':
            self.hysteresisUnder = float(data)
        elif endpoint == 'overshoot':
            self.hysteresisOver = float(data)
        else:
            super.callback(endpoint, data)
