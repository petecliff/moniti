# -*- coding: utf-8 -*-

import os
import json
import logging
import sys
import datetime
from threading import Timer

import greengrasssdk

from bme280 import BME280 # temp, humidity, pressure
from ltr559 import LTR559 # light
from enviroplus import gas
from pms5003 import PMS5003, ReadTimeoutError as pmsReadTimeoutError
from smbus2 import SMBus

TWO_DEC = "{:5.2f}"

READING_INT = 900

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

ggclient = greengrasssdk.client("iot-data")

bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)
pms5003 = PMS5003()
ltr559 = LTR559()

factor = 1.58

def get_cpu_temperature():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        cpu_temp = int(f.read()) / 1000.0
    return cpu_temp

def get_compensated_temperature():
    global cpu_temps
    cpu_temp = get_cpu_temperature()
    cpu_temps = cpu_temps[1:] + [cpu_temp]
    avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
    raw_temp = bme280.get_temperature()
    comp_temp = raw_temp - ((avg_cpu_temp - raw_temp) / factor)
    return TWO_DEC.format(comp_temp)

def get_humidity():
    return TWO_DEC.format(bme280.get_humidity())

def get_pressure():
    return TWO_DEC.format(bme280.get_pressure())

def get_lux():
    return TWO_DEC.format(ltr559.get_lux())

def get_gases():
    gases = {}
    data = gas.read_all()
    gases['oxidising'] = TWO_DEC.format(data.oxidising / 1000)
    gases['reducing'] = TWO_DEC.format(data.reducing / 1000)
    gases['nh3'] = TWO_DEC.format(data.nh3 / 1000)
    return gases

def get_particulates():
    global pms5003
    particulates = {}
    try:
        data = pms5003.read()
    except pmsReadTimeoutError:
        logger.warn("timeout on pms5003")
        pms5003 = pms5003()
        return None
    particulates['ultrafine (PM1.0 ug/m3)'] = TWO_DEC.format(float(data.pm_ug_per_m3(1.0)))
    particulates['combustion particles, organic compounds, metals (PM2.5 ug/m3)'] = TWO_DEC.format(float(data.pm_ug_per_m3(2.5)))
    particulates['dust, pollen, mould spores (PM10 ug/m3)'] = TWO_DEC.format(float(data.pm_ug_per_m3(10.0)))
    return particulates


def send_readings_long_run():
    try:
        ggclient.publish(
            topic = "readings/all",
            queueFullPolicy="AllOrException",
            payload = handler(None, None)
        )
    except Exception as e:
        logger.error("Error publishing message: " + repr(e))

    Timer(READING_INT, send_readings_long_run).start()
    
def handler(event, context):
    values = {}
    values['timestamp'] = datetime.datetime.utcnow().strftime("%Y-%b-%d %H:%M")
    values['temperature'] = get_compensated_temperature()
    values['humidity'] = get_humidity()
    values['pressure'] = get_pressure()
    values['lux'] = get_lux()
    values['gases'] = get_gases()
    values['particulates'] = get_particulates()

    return json.dumps(values)

cpu_temps = [get_cpu_temperature()] * 5
send_readings_long_run()
