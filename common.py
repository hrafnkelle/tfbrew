# common.py
# 
# Changelog:
#  08-FEB-24: Part of fix for loop exception.  Think due to new OS or Python versions (Fix #1)
#
# Ver: 1.0

import asyncio
from aiohttp import web

components = {}

loop = asyncio.get_event_loop()
app = web.Application(loop=loop)

# Export the event loop (Fix #1)
__all__ = ['app', 'loop']
