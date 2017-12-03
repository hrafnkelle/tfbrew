import asyncio
import aiofiles
from aiohttp import web

async def get_temp(sensor=None):
    async with aiofiles.open('/sys/bus/w1/devices/%s/w1_slave'% sensor, mode='r') as sensor_file:
        contents = await sensor_file.read()
    if (contents.split('\n')[0].split(' ')[11] == "YES"):
        temp = float(contents.split("=")[-1]) / 1000
        return temp
    else:
        return -100

async def handle(request):
    temp = await get_temp("28-000004b8240b")
    return web.Response(text="Temp %f"%temp)

app = web.Application()
app.router.add_get('/', handle)

web.run_app(app)
