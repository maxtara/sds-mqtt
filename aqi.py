# "DATASHEET": http://cl.ly/ekot
import serial # pyserial
import struct
import sys
import time
import json
import paho.mqtt.client as mqtt # paho-mqtt
import os 
DEBUG = 0
CMD_MODE = 2
CMD_QUERY_DATA = 4
CMD_DEVICE_ID = 5
CMD_SLEEP = 6
CMD_FIRMWARE = 7
CMD_WORKING_PERIOD = 8
MODE_ACTIVE = 0
MODE_QUERY = 1
PERIOD_CONTINUOUS = 0

JSON_FILE = '/var/www/html/aqi.json'

MQTT_HOST = os.environ['MQTT_HOST']
MQTT_PASSWORD = os.environ['MQTT_PASSWORD']
MQTT_USERNAME = os.environ['MQTT_USERNAME']
MQTT_PORT = int(os.environ['MQTT_PORT'])
MQTT_TOPIC = os.environ['MQTT_TOPIC']
SERIAL_PORT = os.environ['SERIAL_PORT']

COUNT_THING = 5
ser = serial.Serial()
ser.port = SERIAL_PORT
ser.baudrate = 9600

byte, data = 0, ""

# Example working run, set DEBUG to 1
#    > aa b4 06 01 01 00 00 00 00 00 00 00 00 00 00 ff ff 06 ab
#    < c5 06 01 01 00 32 5e 98 ab
#    > aa b4 07 00 00 00 00 00 00 00 00 00 00 00 00 ff ff 05 ab
#    < c5 07 12 0b 10 32 5e c4 ab
#    Y: 18, M: 11, D: 16, ID: 0x5e32, CRC=OK
#    > aa b4 08 01 00 00 00 00 00 00 00 00 00 00 00 ff ff 07 ab
#    < c5 08 01 00 00 32 5e 99 ab
#    > aa b4 02 01 01 00 00 00 00 00 00 00 00 00 00 ff ff 02 ab
#    < c5 02 01 01 00 32 5e 94 ab
#    > aa b4 06 01 01 00 00 00 00 00 00 00 00 00 00 ff ff 06 ab
#    < c5 06 01 01 00 32 5e 98 ab
#    > aa b4 04 00 00 00 00 00 00 00 00 00 00 00 00 ff ff 02 ab
#    < c0 52 00 a9 00 32 5e 8b ab
#    PM2.5:  8.2 , PM10:  16.9
#    > aa b4 04 00 00 00 00 00 00 00 00 00 00 00 00 ff ff 02 ab
#    < c0 52 00 a9 00 32 5e 8b ab
#    PM2.5:  8.2 , PM10:  16.9
#    > aa b4 04 00 00 00 00 00 00 00 00 00 00 00 00 ff ff 02 ab
#    < c0 52 00 a9 00 32 5e 8b ab
#    PM2.5:  8.2 , PM10:  16.9
#    > aa b4 04 00 00 00 00 00 00 00 00 00 00 00 00 ff ff 02 ab
#    < c0 52 00 a9 00 32 5e 8b ab
#    PM2.5:  8.2 , PM10:  16.9
#    > aa b4 04 00 00 00 00 00 00 00 00 00 00 00 00 ff ff 02 ab
#    < c0 52 00 a9 00 32 5e 8b ab
#    PM2.5:  8.2 , PM10:  16.9
#    Publishing using: home/pmsensor/main
#    {"pm10": 16.9, "pm25": 8.2, "time": "22.09.2021 09:31:46"}
#

def dump(d, prefix=b''):
    print(prefix + b' '.join(hex(x).encode()[2:] for x in d))

def construct_command(cmd, data=[]):
    assert len(data) <= 12
    data += [0,]*(12-len(data))
    checksum = (sum(data)+cmd-2)%256
    ret = b"\xaa\xb4" + chr(cmd).encode()
    ret += b''.join(chr(x).encode() for x in data)
    ret += b"\xff\xff" + chr(checksum).encode() + b"\xab"

    if DEBUG:
        dump(ret, b'> ')
    return ret

def process_data(d):
    r = struct.unpack('<HHxxBB', d[2:])
    pm25 = r[0]/10.0
    pm10 = r[1]/10.0
    checksum = sum(v for v in d[2:8])%256
    return [pm25, pm10]
    #print("PM 2.5: {} μg/m^3  PM 10: {} μg/m^3 CRC={}".format(pm25, pm10, "OK" if (checksum==r[2] and r[3]==0xab) else "NOK"))

def process_version(d):
    r = struct.unpack('<BBBHBB', d[3:])
    checksum = sum(v for v in d[2:8])%256
    print("Y: {}, M: {}, D: {}, ID: {}, CRC={}".format(r[0], r[1], r[2], hex(r[3]), "OK" if (checksum==r[4] and r[5]==0xab) else "NOK"))

def read_response():
    byte = 0
    while byte != b"\xaa":
        byte = ser.read(size=1)

    d = ser.read(size=9)

    if DEBUG:
        dump(d, b'< ')
    return byte + d

def cmd_set_mode(mode=MODE_QUERY):
    ser.write(construct_command(CMD_MODE, [0x1, mode]))
    read_response()

def cmd_query_data():
    ser.write(construct_command(CMD_QUERY_DATA))
    d = read_response()
    values = []
    if d[1] == 192:
        values = process_data(d)
    return values

def cmd_set_sleep(sleep):
    mode = 0 if sleep else 1
    ser.write(construct_command(CMD_SLEEP, [0x1, mode]))
    read_response()

def cmd_set_working_period(period):
    ser.write(construct_command(CMD_WORKING_PERIOD, [0x1, period]))
    read_response()

def cmd_firmware_ver():
    ser.write(construct_command(CMD_FIRMWARE))
    d = read_response()
    process_version(d)

def cmd_set_id(id):
    id_h = (id>>8) % 256
    id_l = id % 256
    ser.write(construct_command(CMD_DEVICE_ID, [0]*10+[id_l, id_h]))
    read_response()

def pub_mqtt(jsonrow, client, topic):
    print('Publishing using:', topic)
    print(json.dumps(jsonrow))
    return client.publish(topic, payload=json.dumps(jsonrow))


if __name__ == "__main__":
    ser.open()
    ser.flushInput()

    cmd_set_sleep(0)
    cmd_firmware_ver()
    cmd_set_working_period(PERIOD_CONTINUOUS)
    cmd_set_mode(MODE_QUERY)
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, password=MQTT_PASSWORD)
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    cmd_set_sleep(0)
    for t in range(COUNT_THING):
        values = cmd_query_data();
        if values is not None and len(values) == 2:
            print(f"PM2.5: {values[0]} PM10: {values[1]}")
        else:
            print(f"Error - {values}")


    jsonrow = {'pm25': values[0], 'pm10': values[1], 'time': time.strftime("%d.%m.%Y %H:%M:%S")}
    vv = pub_mqtt(jsonrow, client, MQTT_TOPIC)
    vv.wait_for_publish()
    client.disconnect()
    ser.close()


