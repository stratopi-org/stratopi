import serial
import time
import RPi.GPIO as GPIO
from lib import log
from lib import common
from datetime import datetime


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


def get():
    try:
        response = send_at('AT+CGPSINFO', '+CGPSINFO: ')

        # no GPS fix response is ,,,,,,,,
        if ',,,,,,,,' in response:
            warning_message = f"no GPS fix"
            log.warning(warning_message)
            raise serial.SerialException(warning_message)

        return response
    except serial.SerialException:
        try:
            send_at('AT+CGPS=1,1', 'OK')
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

    return decimal_value


def parse_direction(_course):
    # 'N' twice in the list is NOT a bug but a deliberate decision
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N']
    index = int((_course + 22.5) % 360 // 45)
    return directions[index]


def parse(_data):
    try:
        data = common.strip_list_elements(_data.split('+CGPSINFO:'))
        data = data[1].replace('\r\n\r\nOK', '').strip()
        data_fields = data.split(',')

        if len(data_fields) == 9:
            date_utc = datetime.strptime(data_fields[4], '%d%m%y').date()
            time_utc = datetime.strptime(data_fields[5], '%H%M%S.%f').time()
            latitude = parse_coordinate(data_fields[0], data_fields[1])
            longitude = parse_coordinate(data_fields[2], data_fields[3])
            altitude_meters = float(data_fields[6])
            altitude_feet = common.meters_to_feet(altitude_meters)
            speed_ms = float(data_fields[7])
            speed_knots = common.mps_to_knots(speed_ms)
            speed_mph = common.mps_to_mph(speed_ms)
            course = float(data_fields[8])
            direction = parse_direction(course)

            return {
                "Date (UTC)": date_utc,
                "Time (UTC)": time_utc,
                "Latitude": latitude,
                "Longitude": longitude,
                "Altitude (m)": altitude_meters,
                "Altitude (ft)": altitude_feet,
                "Speed (m/s)": speed_ms,
                "Speed (knots)": speed_knots,
                "speed (mph)": speed_mph,
                "Course (deg)": course,
                "Direction": direction
            }
    except (ValueError, IndexError, TypeError) as err:
        log.error(err)
        pass

    return None


def power_off(power_key=6):
    log.info('GPS is powering off...')
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(1)
    log.info('GPS powered off')
