import asyncio
import aiofiles
from aiohttp import web
import time

class PIDArduino(object):

    def __init__(self, sampleTimeSec, kp, ki, kd, outputMin=float('-inf'),
                 outputMax=float('inf'), getTimeMs=None):
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
        self._Ki = ki * sampleTimeSec
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

        if (now - self._lastCalc) < self._sampleTime:
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
        return time.time() * 1000


class Heater:
    def __init__(self):
        self.power = 0.0

    async def get(self, request):
        return web.Response(text="%f"%self.power)

    async def post(self, request):
        power_str = await request.text()
        self.power = float(power_str)
        return web.Response()

class Sensor:
    def __init__(self, sensorId):
        self.sensorId = sensorId


    async def get_temp(self, sensor=None):
        await asyncio.sleep(2)
        return 24.0
#        async with aiofiles.open('/sys/bus/w1/devices/%s/w1_slave'% sensor, mode='r') as sensor_file:
#            contents = await sensor_file.read()
#        if (contents.split('\n')[0].split(' ')[11] == "YES"):
#            temp = float(contents.split("=")[-1]) / 1000
#            return temp
#        else:
#            return -100


    async def get(self, request):
        temp = await self.get_temp(self.sensorId)
        return web.Response(text="%f"%temp)

class Controller:
    def __init__(self, sensor, actor):
        self.state = 'off'
        self.sensor = sensor
        self.actor = actor
        self.targetTemp = 0.0
        self.pid = PIDArduino(10, 50, 0.5, 10, 0, 100)

    async def getState(self, request):
        return web.Response(text=self.state)

    async def postState(self, request):
        self.state = request.match_info['state']
        return web.Response(text=self.state)

    async def postTemp(self, request):
        self.targetTemp = float(await request.text())
        print("Target temp set to: %f"%self.targetTemp)
        return web.Response(text=str(self.targetTemp))

    async def getTemp(self, request):
        return web.Response(text=str(self.targetTemp))

    async def run(self):
        if self.state == 'on':
            inputTemp = await self.sensor.get_temp()
            output = self.pid.calc(inputTemp, self.targetTemp)
            self.actor.power = output
        else:
            self.actor.power = 0.0
            await asyncio.sleep(1)

sensor = Sensor("28-000004b8240b") 
heater = Heater()
ctrl=Controller(sensor, heater)

async def controller_runner(app):
    while True:
        await ctrl.run()


async def start_background_tasks(app):
    app['controller_runner'] = app.loop.create_task(controller_runner(app))

async def cleanup_background_tasks(app):
    app['controller_runner'].cancel()
    await app['controller_runner']

async def index(request):
    return web.FileResponse('index.html')

app = web.Application()
app.on_startup.append(start_background_tasks)
app.on_cleanup.append(cleanup_background_tasks)

app.router.add_get('/sensor', sensor.get)
app.router.add_routes([web.get('/heater', heater.get), web.post('/heater', heater.post)])
app.router.add_get('/controller', ctrl.getState)
app.router.add_post('/controller/target', ctrl.postTemp)
app.router.add_get('/controller/target', ctrl.getTemp)
app.router.add_post('/controller/{state}',ctrl.postState)
app.router.add_get('/',index)


web.run_app(app)
