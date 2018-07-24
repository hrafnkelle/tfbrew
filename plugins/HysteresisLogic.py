import interfaces

def factory(name, settings):
    hysteresisOver = settings.get('allowedOvershoot', 0.5)
    hysteresisUnder = settings.get('allowedUndershoot', 0.5)
    keepHot = not settings.get('keepCold', True)
    keepHot = settings.get('keepHot', keepHot)
    if keepHot:
        return HysteresisHeatingLogic(hysteresisOver, hysteresisUnder)
    else:
        return HysteresisCoolingLogic(hysteresisOver, hysteresisUnder)


class HysteresisCoolingLogic(interfaces.Logic):
    def __init__(self, hysteresisUnder=0.5, hysteresisOver=0.5):
        self.hysteresisUnder = hysteresisUnder
        self.hysteresisOver = hysteresisOver
        self.lastOutput = 0
        self.output = 0

    def shouldAct(self, currentTemp, threshold):
        if self.lastOutput == 1:
            threshold = threshold - self.hysteresisUnder
        else:
            threshold = threshold + self.hysteresisOver

        if currentTemp >= threshold:
            return 1
        else:
            return 0

    def calc(self, input, setpoint):
        self.output = self.shouldAct(input, setpoint)
        self.lastOutput = self.output
        return self.output*100.0

    def callback(self, endpoint, data):
        if endpoint == 'undershoot':
            self.hysteresisUnder = float(data)
        elif endpoint == 'overshoot':
            self.hysteresisOver = float(data)
        else:
            super.callback(endpoint, data)

class HysteresisHeatingLogic(HysteresisCoolingLogic):
    def shouldAct(self, currentTemp, threshold):
        if self.lastOutput == 1:
            threshold = threshold + self.hysteresisOver
        else:
            threshold = threshold - self.hysteresisUnder

        if currentTemp <= threshold:
            return 1
        else:
            return 0
