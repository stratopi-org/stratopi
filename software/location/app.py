import signal
import sys
import time
from lib import gps

signal.signal(signal.SIGINT, lambda sig, frame: (gps.power_off(), sys.exit(0)))
gps.power_on()

while True:
    gps_result = gps.get_gps()

    if gps_result:
        print(gps_result)

    time.sleep(3)
