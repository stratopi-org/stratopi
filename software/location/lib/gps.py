import serial
import time
import RPi.GPIO as GPIO

ser = serial.Serial('/dev/ttyS0', baudrate=115200)
ser.flushInput()


def send_at(command, expected_response, timeout):
    ser.write((command + '\r\n').encode())
    start_time = time.time()
    rec_buff = b''  # Use bytes for receiving data
    while time.time() - start_time < timeout:
        rec_buff += ser.read(ser.inWaiting())
        if expected_response.encode() in rec_buff:
            return rec_buff.decode().strip()
        time.sleep(0.02)

    rec_buff = rec_buff.decode()
    raise serial.SerialException(f"'{rec_buff}'' is not in response of '{expected_response}'")


def get_gps_position():
    send_at('AT+CGPS=1,1', 'OK', 1)
    return send_at('AT+CGPSINFO', '+CGPSINFO: ', 1)


def power_on(power_key=6):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(power_key, GPIO.OUT)
    time.sleep(0.1)
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(1)
    ser.flushInput()


def power_down(power_key=6):
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(1)
