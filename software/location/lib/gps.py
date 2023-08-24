import time
import serial
import RPi.GPIO as GPIO
import random
from lib import log

ser = serial.Serial('/dev/ttyS0', baudrate=115200)
ser.flushInput()


def power_on(power_key=6):
    log.info('GPS is powering on...')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(power_key, GPIO.OUT)
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(1)
    log.info('GPS powered on')


def send_at(_command, _expected_response, timeout=1):
    ser.write(f"{_command}\r\n".encode())
    log.debug(f"sent '{_command}' from serial")

    start_time = time.time()
    rec_buff = b''  # Use bytes for receiving data

    while time.time() - start_time < timeout:
        rec_buff += ser.read(ser.in_waiting)
        if _expected_response.encode() in rec_buff:
            return rec_buff.decode().strip()
        time.sleep(0.05)

    rec_buff = rec_buff.decode().strip()
    warning_message = f"serial command '{_command}' did not receive '{_expected_response}'"
    log.warning(warning_message)
    raise serial.SerialException(warning_message)


def get_gps():
    try:
        response = send_at('AT+CGPSINFO', '+CGPSINFO: ')

        if ',,,,,,,,' in response:
            warning_message = f"no GPS fix"
            log.warning(warning_message)
            raise serial.SerialException(warning_message)

        return response
    except serial.SerialException:
        send_at_fn = random.choice([lambda: send_at('AT+CGPS=1,1', 'OK'),
                                    lambda: send_at('AT+CGPS=0', 'OK')])

        try:
            send_at_fn()
            return False
        except serial.SerialException:
            return False


def power_off(power_key=6):
    log.info('GPS is powering off...')
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(1)
    log.info('GPS powered off')
