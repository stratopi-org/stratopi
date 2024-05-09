import serial
import time
import RPi.GPIO as GPIO
from lib import log
from lib import common
from datetime import datetime


ser = serial.Serial('/dev/ttyS0', baudrate=115200)
ser.flushInput()


def power_on(power_key=6, sleep_delay=0.5):
    log.info('GPS is powering on...')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(power_key, GPIO.OUT)
    time.sleep(sleep_delay)
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(sleep_delay)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(sleep_delay)
    log.info('GPS powered on')


def send_at(_command, _expected_response, timeout=1):
    ser.write(f"{_command}\r\n".encode())
    log.debug(f"sent command '{_command}' via serial")

    start_time = time.time()
    rec_buff = b''  # use bytes for receiving data

    while time.time() - start_time < timeout:
        rec_buff += ser.read(ser.in_waiting)
        if _expected_response.encode() in rec_buff:
            return rec_buff.decode().strip()
        time.sleep(0.05)

    warning_message = f"serial command '{_command}' did not return expected response '{_expected_response}'"
    log.warning(warning_message)
    raise serial.SerialException(warning_message)


def get():
    try:
        response = send_at('AT+CGPSINFO', '+CGPSINFO: ')

        # no GPS fix response is ,,,,,,,,
        if ',,,,,,,,' in response:
            return False

        return response
    except serial.SerialException:
        pass

    return False


def parse_coordinate(_coord_str, _hemisphere):
    dms_value = float(_coord_str)

    degrees = int(dms_value // 100)
    minutes = dms_value % 100

    decimal_value = degrees + (minutes / 60)

    if _hemisphere.upper() in ('S', 'W'):
        decimal_value = -decimal_value

    return "{:.5f}".format(decimal_value)


def parse_direction(_course):
    if not isinstance(_course, float):
        raise ValueError('course must in degress and a float')

    if _course < 0 or _course > 360:
        raise ValueError('course must be between 0 and 360 degrees')

    # 'N' twice in the list is NOT a bug but a deliberate decision
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N']
    index = int((_course + 22.5) % 360 // 45)
    return directions[index]


def parse(_data):
    if not _data:
        return None

    try:
        data = common.strip_list_elements(_data.split('+CGPSINFO:'))
        data = data[1].replace('\r\n\r\nOK', '').strip()
        data_fields = data.split(',')

        if len(data_fields) == 9:
            date = datetime.strptime(data_fields[4], '%d%m%y').date()
            time = datetime.strptime(data_fields[5], '%H%M%S.%f').time()
            latitude = parse_coordinate(data_fields[0], data_fields[1])
            longitude = parse_coordinate(data_fields[2], data_fields[3])
            satellites = int(data_fields[5])
            altitude_m = "{:.1f}".format(float(data_fields[6]))
            speed_kn = "{:.1f}".format(float(data_fields[7]))
            course_d = "{:.1f}".format(float(data_fields[8]))
            direction = parse_direction(float(course_d))

            return {
                "date": date,
                "time": time,
                "coordinates": (latitude, longitude),
                "satellites": satellites,
                "altitude_m": altitude_m,
                "speed_kn": speed_kn,
                "course_d": course_d,
                "direction": direction
            }
    except (ValueError, IndexError, TypeError) as err:
        log.error(err)
        pass

    return None


def power_off(power_key=6, sleep_delay=0.5):
    log.info('GPS is powering off...')
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(sleep_delay)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(sleep_delay)
    log.info('GPS powered off')
