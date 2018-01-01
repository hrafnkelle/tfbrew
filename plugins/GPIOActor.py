from interfaces import Actor

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

def factory(name, settings):
    return GPIOActor(name, settings['gpio'], settings['pwmFrequency'])


class GPIOActor(Actor):
    def __init__(self, name, pin, pwmFrequency):
        self.name = name
        self.power = 0.0
        self.pin = pin
        self.frequency = pwmFrequency
        GPIO.setup(self.pin, GPIO.OUT)
        self.p = GPIO.PWM(self.pin, self.frequency)
        self.p.start(self.power)

    def updatePower(self, power):
        self.power = power
        self.p.ChangeDutyCycle(self.power)

    def on(self):
        self.updatePower(100.0)

    def off(self):
        self.updatePower(0.0)

    def callback(self, endpoint, data):
        if endpoint == 'state':
            if data == 0:
                print("Turning %s off"%self.name)
                self.off()
            elif data == 1:
                print("Turning %s on"%self.name)
                self.on()
            else:
                print("Warning: GPIOActor:%s unsupported data value: %d"%(self.name, data))
