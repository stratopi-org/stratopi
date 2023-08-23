import RPi.GPIO as GPIO
import serial
import time

ser = serial.Serial('/dev/ttyS0', 115200)
ser.flushInput()


def send_at(command, back, timeout):
    ser.write((command + '\r\n').encode())
    start_time = time.time()
    rec_buff = b''  # Use bytes for receiving data
    while time.time() - start_time < timeout:
        rec_buff += ser.read(ser.inWaiting())
        if back.encode() in rec_buff:
            rec_buff = rec_buff.decode()
            print(rec_buff)
            return 1
        time.sleep(0.01)
    rec_buff = rec_buff.decode()
    print(command + ' ERROR')
    print(command + ' back:\t' + rec_buff)
    return 0


def get_gps_position():
    send_at('AT+CGPS=1,1', 'OK', 1)
    time.sleep(1)
    while True:
        rec_buff = ''
        answer = send_at('AT+CGPSINFO', '+CGPSINFO: ', 1)
        if answer == 1:
            if ',,,,,,' in rec_buff:
                print('GPS is not ready')
                time.sleep(5)
                continue
        else:
            print('error %d' % answer)
            send_at('AT+CGPS=0', 'OK', 1)
            return False
        time.sleep(5)


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


try:
    power_on()
    get_gps_position()
    power_down()
except:
    if ser != None:
        ser.close()
    power_down()
    GPIO.cleanup()

    if ser != None:
        ser.close()
        GPIO.cleanup()
