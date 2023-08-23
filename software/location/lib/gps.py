import time
import serial
import RPi.GPIO as GPIO
from lib import log

ser = serial.Serial('/dev/ttyS0', baudrate=115200)
ser.flushInput()


def send_at(command, expected_response, timeout=1):
    ser.write((command + '\r\n').encode())
    log.debug(f"sent '{command}' from serial")
    start_time = time.time()
    rec_buff = b''  # Use bytes for receiving data
    while time.time() - start_time < timeout:
        rec_buff += ser.read(ser.inWaiting())
        if expected_response.encode() in rec_buff:
            return rec_buff.decode().strip()
        time.sleep(0.05)

    rec_buff = rec_buff.decode().strip()
    log.warning(f"serial command '{command}' did not respond back with '{expected_response}'")
    raise serial.SerialException(f"'{rec_buff}' is not in serial response of '{expected_response}'")


def get_gps_position():
    try:
        send_at('AT+CGPS=1,1', 'OK')
    except serial.SerialException as err:
        send_at('AT+CGPS=0', 'OK')

    return send_at('AT+CGPSINFO', '+CGPSINFO: ')


def power_on(power_key=6):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(power_key, GPIO.OUT)
    time.sleep(0.5)
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(1)
    ser.flushInput()


def power_off(power_key=6):
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(1)
