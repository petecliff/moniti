import json
import os
import requests

ID = os.getenv('LUFTDATEN_ID')

# Send to luftdaten - based on:
# https://github.com/pimoroni/enviroplus-python/blob/master/examples/luftdaten.py
# This is triggered from MQTT with IoT Core action in AWS.
# However, could also add to the readings sender to send direct from the Pi.

def handler(event, context):
    pm_values = [
        {'value_type': 'P2', 'value': event['pm2.5']},
        {'value_type': 'P1', 'value': event['pm10.0']}
    ]

    temp_values = [
        {'value_type': 'temperature', 'value': event['temperature']},
        {'value_type': 'humidity', 'value': event['humidity']},
        {'value_type': 'pressure', 'value': event['pressure'] }
    ]

    resp_1 = requests.post(
        "https://api.luftdaten.info/v1/push-sensor-data/",
        json={
            "software_version": "enviro-plus 0.0.1",
            "sensordatavalues": pm_values
        },
        headers={
            "X-PIN": "1",
            "X-Sensor": ID,
            "Content-Type": "application/json",
            "cache-control": "no-cache"
        }
    )

    resp_2 = requests.post(
        "https://api.luftdaten.info/v1/push-sensor-data/",
        json={
            "software_version": "enviro-plus 0.0.1",
            "sensordatavalues": temp_values
        },
        headers={
            "X-PIN": "11",
            "X-Sensor": ID,
            "Content-Type": "application/json",
            "cache-control": "no-cache"
        }
    )

    if resp_1.ok and resp_2.ok:
        print("Sent OK")
    else:
        print("Send error")
        print(pm_values)
        print(temp_values)

    return "Done"


    