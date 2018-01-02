"""
PID Control for the masses
"""
# This code is based on the Arduino-PID-Library 
# https://github.com/br3ttb/Arduino-PID-Library
#
# The original PID Arduino library was written by Brett Beauregard <br3ttb@gmail.com> brettbeauregard.com
# which is licensed under the MIT license
#

import time
from interfaces import Logic


def factory(name, settings):
    kp = settings['p']
    ki = settings['i']
    kd = settings['d']
    logic = PIDLogic(10.0, kp, ki, kd, 0, 100)
    return logic

class PIDLogic(Logic):
    def __init__(self, sampleTimeSec, kp, ki, kd, outputMin=float('-inf'), outputMax=float('inf'), getTimeMs=None):
        if kp is None:
            raise ValueError('kp must be specified')
        if ki is None:
            raise ValueError('ki must be specified')
        if kd is None:
            raise ValueError('kd must be specified')
        if sampleTimeSec <= 0:
            raise ValueError('sampleTimeSec must be greater than 0')
        if outputMin >= outputMax:
            raise ValueError('outputMin must be less than outputMax')

        self._Kp = kp
        self._Ki = sampleTimeSec / ki
        self._Kd = kd / sampleTimeSec
        self._sampleTime = sampleTimeSec * 1000
        self._outputMin = outputMin
        self._outputMax = outputMax
        self._iTerm = 0
        self._lastInput = 0
        self._lastOutput = 0
        self._lastCalc = 0

        if getTimeMs is None:
            self._getTimeMs = self._currentTimeMs
        else:
            self._getTimeMs = getTimeMs

    def reset():
        self._iTerm = 0.0

    def calc(self, inputValue, setpoint):
        now = self._getTimeMs()

        diff = now - self._lastCalc
        # print("now: %d lastCalc %d diff %d <? sampleTime %d"%(now, self._lastCalc,  diff, self._sampleTime))
        if (now - self._lastCalc) < 0.9*self._sampleTime:
            # print("not yet")
            return self._lastOutput

        # Compute all the working error variables
        error = setpoint - inputValue
        dInput = inputValue - self._lastInput

        # In order to prevent windup, only integrate if the process is not saturated
        if self._lastOutput < self._outputMax and self._lastOutput > self._outputMin:
            self._iTerm += self._Ki * error
            self._iTerm = min(self._iTerm, self._outputMax)
            self._iTerm = max(self._iTerm, self._outputMin)

        p = self._Kp * error
        i = self._iTerm
        d = -(self._Kd * dInput)

        # Compute PID Output
        self._lastOutput = p + i + d
        self._lastOutput = min(self._lastOutput, self._outputMax)
        self._lastOutput = max(self._lastOutput, self._outputMin)

        # Remember some variables for next time
        self._lastInput = inputValue
        self._lastCalc = now
        return self._lastOutput

    def _currentTimeMs(self):
        val = time.time() * 1000
        # print("_currentTimeMs: %d"%val)
        return val
