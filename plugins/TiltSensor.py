import asyncio
import datetime
import logging
import aioblescan as aiobs
from decimal import Decimal, ROUND_HALF_UP
from event import notify, Event
from collections import deque

logger = logging.getLogger(__name__)

# Mapping of Tilt colors to their UUIDs
tilt_colors = {
    'Red':    "a495bb10-c5b1-4b44-b512-1370f02d74de",
    'Green':  "a495bb20-c5b1-4b44-b512-1370f02d74de",
    'Black':  "a495bb30-c5b1-4b44-b512-1370f02d74de",
    'Purple': "a495bb40-c5b1-4b44-b512-1370f02d74de",
    'Orange': "a495bb50-c5b1-4b44-b512-1370f02d74de",
    'Blue':   "a495bb60-c5b1-4b44-b512-1370f02d74de",
    'Yellow': "a495bb70-c5b1-4b44-b512-1370f02d74de",
    'Pink':   "a495bb80-c5b1-4b44-b512-1370f02d74de",
}

# Lookup tables for color mappings
color_lookup_table = {}
color_lookup_table_no_dash = {}

# Function to lookup color by UUID
def color_lookup(color):
    global color_lookup_table, color_lookup_table_no_dash
    if not color_lookup_table:
        color_lookup_table = {tilt_colors[x]: x for x in tilt_colors}
    if not color_lookup_table_no_dash:
        color_lookup_table_no_dash = {tilt_colors[x].replace("-", ""): x for x in tilt_colors}
    return color_lookup_table.get(color, color_lookup_table_no_dash.get(color))

# Factory function to create TiltSensor instances
def factory(name, settings):
    return TiltSensor(name, settings['color'], settings['tempclbr'], settings['gravclbr'], settings['startgrav'], settings['sendtime'])

# Conversion functions for various brewing calculations
def to_celsius(fahrenheit):
    return round((fahrenheit - 32.0) / 1.8, 2)

def to_brix(sg):
    sg = Decimal(sg)
    brix = (((Decimal('182.4601') * sg - Decimal('775.6821')) * sg + Decimal('1262.7794')) * sg - Decimal('669.5622'))
    return brix.quantize(Decimal('0.01'))

def to_abv(sg, stgrav):
    sg = Decimal(sg)
    stgrav = Decimal(stgrav)
    abv = (stgrav - sg) * Decimal('131.25')
    return abv.quantize(Decimal('0.01'))

def to_atten(sg, stgrav):
    sg = Decimal(sg)
    stgrav = Decimal(stgrav)
    atten = Decimal('100') * ((stgrav - sg) / (stgrav - Decimal('1')))
    return atten.quantize(Decimal('0.01'))

# TiltSensor class handles data processing and notification for a specific Tilt hydrometer
class TiltSensor:
    def __init__(self, name, color, tempcalbr, gravcalbr, startgrav, sendtime):
        if color not in tilt_colors:
            raise ValueError("Invalid color specified")

        self.name = name
        self.color = color
        self.temp_offset = Decimal(tempcalbr).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.gravity_offset = Decimal(gravcalbr).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        self.start_gravity = Decimal(startgrav).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        self.sendtime = sendtime
        self.last_sendtime = datetime.datetime.min
        self.dev_id = 0
        self.smoothing_window = 60
        self.gravity_list = deque(maxlen=self.smoothing_window)
        self.temp_list = deque(maxlen=self.smoothing_window)
        self.last_value_received = datetime.datetime.now() - self._cache_expiry_seconds()
        self.gravity = Decimal(0.0)
        self.temp = Decimal(0.0)
        self.rssi = 0
        self.tilt_pro = False

        try:
            self.sock = aiobs.create_bt_socket(self.dev_id)
            print(f"Created Bluetooth socket")
        except OSError as e:
            logger.error(f"Unable to create socket - {e}. Is there a Bluetooth adapter attached?")
            while True:
                time.sleep(60)
            exit(1)

        asyncio.get_event_loop().create_task(self.run())

    def _cache_expiry_seconds(self) -> datetime.timedelta:
        return datetime.timedelta(seconds=(self.smoothing_window * 1.2 * 4))

    def expired(self) -> bool:
        return self.last_value_received <= datetime.datetime.now() - self._cache_expiry_seconds()

    def _add_to_list(self, gravity, temp):
        if self.expired():
            self.gravity_list.clear()
            self.temp_list.clear()
        self.last_value_received = datetime.datetime.now()
        self.gravity_list.append(gravity)
        self.temp_list.append(temp)

    @staticmethod
    def _average_deque(d: deque) -> float:
        if not d:
            return 0.0
        return sum(d) / len(d)

    def smoothed_gravity(self) -> Decimal:
        return Decimal(self._average_deque(self.gravity_list)).quantize(Decimal('.0001' if self.tilt_pro else '.001'))

    def smoothed_temp(self) -> Decimal:
        return Decimal(self._average_deque(self.temp_list)).quantize(Decimal('.1' if self.tilt_pro else '1.'))

    async def run(self):
        event_loop = asyncio.get_running_loop()
        conn, btctrl = await event_loop._create_connection_transport(self.sock, aiobs.BLEScanRequester, None, None)
        
        # Process BLE beacon data
        def process_ble_beacon(data):
            ev = aiobs.HCI_Event()
            try:
                ev.decode(data)
            except:
                return False

            if ev.raw_data is None:
                #logger.debug("Event has no raw data")
                return False

            raw_data_hex = ev.raw_data.hex()

            if len(raw_data_hex) < 80 or "1370f02d74de" not in raw_data_hex:
                return False

            try:
                manufacturer_data = ev.retrieve("Manufacturer Specific Data")
                if not manufacturer_data:
                    return False
                payload = manufacturer_data[0].payload[1].val.hex()

                uuid = payload[4:36]
                color = color_lookup(uuid)
                if color is None or color != self.color:
                    return False

                temp = int.from_bytes(bytes.fromhex(payload[36:40]), byteorder='big')
                gravity = int.from_bytes(bytes.fromhex(payload[40:44]), byteorder='big')
                rssi = ev.retrieve("rssi")[-1].val

                if gravity >= 5000:
                    self.tilt_pro = True
                    gravity = Decimal(gravity) / 10000
                    temp = Decimal(temp) / 10
                else:
                    self.tilt_pro = False
                    gravity = Decimal(gravity) / 1000
                    temp = Decimal(temp)

                gravity += self.gravity_offset
                temp += self.temp_offset

                self._add_to_list(gravity, temp)

                # Check if the notify interval has passed before sending notifications
                current_time = datetime.datetime.now()
                if (current_time - self.last_sendtime).total_seconds() >= self.sendtime:
                    notify(Event(source=self.name, endpoint='temperature', data=temp))
                    notify(Event(source=self.name, endpoint='gravity', data=gravity))
                    notify(Event(source=self.name, endpoint='brix', data=to_brix(gravity)))
                    notify(Event(source=self.name, endpoint='abv', data=to_abv(gravity, self.start_gravity)))
                    notify(Event(source=self.name, endpoint='atten', data=to_atten(gravity, self.start_gravity)))
                    notify(Event(source=self.name, endpoint='ograv', data=self.start_gravity))
                    self.last_sendtime = current_time

            except Exception as e:
                logger.error(e)
                return False

        btctrl.process = process_ble_beacon
        await btctrl.send_scan_request()

        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logger.info('Keyboard interrupt')
        finally:
            logger.debug('Closing event loop')
            await btctrl.stop_scan_request()
            command = aiobs.HCI_Cmd_LE_Advertise(enable=False)
            await btctrl.send_command(command)
            conn.close()
