import signal
import time
from lib import gps

signal.signal(signal.SIGINT, lamdba sig, frame: gps.power_off())
gps.power_on()

while True:
    gps_result = gps.get_gps()

    if gps_result:
        print(gps_result)

    time.sleep(3)
