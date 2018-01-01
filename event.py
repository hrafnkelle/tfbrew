import asyncio
from collections import namedtuple

Event = namedtuple('Event',['source','endpoint','data'])

def name(event):
    return "%s.%s"%(event.source, event.endpoint)

Event.name = name

observers = {}

def register(eventName, callback):
    observers.setdefault(eventName, []).append(callback)

def notify(event):
    print("notify %s"%str(event))
    if event.name() in observers:
        for observer in observers[event.name()]:
            if asyncio.iscoroutinefunction(observer):
                asyncio.ensure_future(observer(event.data))
            else:
                observer(event.data)
