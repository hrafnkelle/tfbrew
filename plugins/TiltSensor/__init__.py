# ../TiltSensor/__init__.py
# 
# Changelog:
#  08-FEB-24: Added temp/gravity calibration, starting grav, abv, attenuation, and brix. Changed return value to Fahrenheit not Celsius. Clean up work.
#
# Ver: 1.0

import asyncio
import sys
import datetime
import time
import logging

import bluetooth._bluetooth as bluez

import TiltSensor.blescan as blescan

import interfaces
from event import notify, Event

logger = logging.getLogger(__name__)

def factory(name, settings):
   return TiltSensor(name, settings['color'], settings['tempclbr'], settings['gravclbr'], settings['startgrav'])


TILTS = {
        'a495bb10c5b14b44b5121370f02d74de': 'Red',
        'a495bb20c5b14b44b5121370f02d74de': 'Green',
        'a495bb30c5b14b44b5121370f02d74de': 'Black',
        'a495bb40c5b14b44b5121370f02d74de': 'Purple',
        'a495bb50c5b14b44b5121370f02d74de': 'Orange',
        'a495bb60c5b14b44b5121370f02d74de': 'Blue',
        'a495bb70c5b14b44b5121370f02d74de': 'Yellow',
        'a495bb80c5b14b44b5121370f02d74de': 'Pink',
}


def distinct(objects):
    seen = set()
    unique = []
    for obj in objects:
        if obj['uuid'] not in seen:
            unique.append(obj)
            seen.add(obj['uuid'])
    return unique


def to_celsius(fahrenheit):
    return round((fahrenheit - 32.0) / 1.8, 2)

def to_brix(sg):
    brix = round((((182.4601*sg  -775.6821)*sg + 1262.7794)*sg - 669.5622), 2)
    return brix

def to_abv(sg,stgrav):
    abv = round((stgrav - sg) * 131.25, 2)
    return abv

def to_atten(sg,stgrav):
    atten = round(100 * ((stgrav - sg)/(stgrav - 1)), 2)
    return atten

class TiltSensor(interfaces.Sensor):
    def __init__(self, name, color, tempcalbr, gravcalbr, startgrav):
       self.name = name
       self.color = color
       self.tempcalbr = tempcalbr
       self.gravcalbr = gravcalbr
       self.startgrav = startgrav
       self.dev_id = 0
       self.lastTemp = 0.0
       self.lastGravity = 1.0
       try:
           self.sock = bluez.hci_open_dev(self.dev_id)
           logger.info('Starting pytilt logger')
           blescan.hci_le_set_scan_parameters(self.sock)
           blescan.hci_enable_le_scan(self.sock)
       except:
           logger.error('error accessing bluetooth device...')

       asyncio.get_event_loop().create_task(self.run())

    async def run(self):
        while True:
            (temp, gravity) = await asyncio.get_event_loop().run_in_executor(None, self.monitor_tilt)
            gravity = gravity + self.gravcalbr
            temp = temp + self.tempcalbr
            self.lastTemp = temp
            self.lastGravity = gravity/1000.0
            notify(Event(source=self.name, endpoint='temperature', data=temp))
            notify(Event(source=self.name, endpoint='gravity', data=gravity/1000.0))
            notify(Event(source=self.name, endpoint='abv', data=to_abv(gravity/1000.0, self.startgrav)))
            notify(Event(source=self.name, endpoint='atten', data=to_atten(gravity/1000.0, self.startgrav)))
            notify(Event(source=self.name, endpoint='ograv', data=self.startgrav))
            notify(Event(source=self.name, endpoint='brix', data=to_brix(gravity/1000.0)))

    def monitor_tilt(self):
        while True:
            beacons = distinct(blescan.parse_events(self.sock, 10))
            for beacon in beacons:
                if beacon['uuid'] in TILTS.keys() and TILTS[beacon['uuid']] == self.color:
                    #Change reutrn value to Fahrenheit. Original line kept for flexibility
                    #return (to_celsius(beacon['major']), beacon['minor'])
                    return (beacon['major'], beacon['minor'])
    
    def temp(self):
        return self.lastTemp

    def gravity(self):
        return self.lastGravity
