"""
Backend for a yet another brewing application controlled by a Blynk frontend
"""

import sys, os
import importlib
import logging

import asyncio
from aiohttp import web
from ruamel.yaml import YAML

import interfaces
import controller
import event

logging.basicConfig(level=logging.DEBUG)


sys.path.append(os.path.join(os.path.dirname(__file__), "plugins"))

app = web.Application()


components = {}
controllers = {}

yaml = YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
config = yaml.load(open('config.yaml',mode='r'))
for componentType in ['sensors', 'actors', 'extensions']:
    for sensor in config[componentType]:
        for name, attribs in sensor.items():
            print("setting up %s"%name)
            plugin = importlib.import_module('plugins.%s'%attribs['plugin'])
            components[name] = plugin.factory(name, attribs)
for ctrl in config['controllers']:
    for name, attribs in ctrl.items():
        logicPlugin = importlib.import_module('plugins.%s'%attribs['plugin'])
        logic = logicPlugin.factory(name, attribs['logicCoeffs'])
        sensor = components[attribs['sensor']]
        actor = components[attribs['actor']]
        initialSetpoint = attribs.get('initialSetpoint', 67.0)
        initialState = 'on' if attribs.get('initialState', False) else 'off'
        components[name] = controller.Controller(name, sensor, actor, logic, initialSetpoint, initialState)
        print("setting up %s"%name)


for conn in config['connections']:
    (sendEvent, recvEvent) = conn.split('=>')
    (sendComponent, sendType) = sendEvent.split('.')
    (recvComponent, recvType) = recvEvent.split('.')
    print("About to register %s to %s type %s"%(sendComponent, recvComponent, recvType))
    event.register(sendEvent, lambda event, rc=recvComponent, rt=recvType: components[rc].callback(rt, event))

async def start_background_tasks(app):
    pass

async def cleanup_background_tasks(app):
    pass

app.on_startup.append(start_background_tasks)
app.on_cleanup.append(cleanup_background_tasks)

web.run_app(app)
