import asyncio
import sys
import datetime
import time

import bluetooth._bluetooth as bluez

import TiltSensor.blescan as blescan

import interfaces
from event import notify, Event

def factory(name, settings):
   return TiltSensor(name)


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
    brix = (((182.4601*sg  -775.6821)*sg + 1262.7794)*sg - 669.5622)
    return brix

class TiltSensor(interfaces.Sensor):
    def __init__(self, name):
       self.name = name
       self.dev_id = 0
       try:
           self.sock = bluez.hci_open_dev(self.dev_id)
           print('Starting pytilt logger')
           blescan.hci_le_set_scan_parameters(self.sock)
           blescan.hci_enable_le_scan(self.sock)
       except:
           print('error accessing bluetooth device...')

       asyncio.get_event_loop().create_task(self.run())

    async def run(self):
        while True:
            (temp, gravity) = await asyncio.get_event_loop().run_in_executor(None, self.monitor_tilt)
            notify(Event(source=self.name, endpoint='temperature', data=temp))
            notify(Event(source=self.name, endpoint='gravity', data=gravity/1000.0))
            notify(Event(source=self.name, endpoint='brix', data=to_brix(gravity/1000.0)))

    def monitor_tilt(self):
        while True:
            beacons = distinct(blescan.parse_events(self.sock, 10))
            for beacon in beacons:
                if beacon['uuid'] in TILTS.keys():
#                     print({
#                         'color': TILTS[beacon['uuid']],
#                         'timestamp': datetime.datetime.now().isoformat(),
#                         'temp': to_celsius(beacon['major']),
#                         'gravity': beacon['minor']
#                     })
                    return (to_celsius(beacon['major']), beacon['minor'])
            print("INFO: Nothing found from bluetooth")
    
