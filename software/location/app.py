import sys
import signal
import time
from lib import gps

signal.signal(signal.SIGINT, lambda sig, frame: (gps.power_off(), sys.exit(0)))
gps.power_on()

while True:
    result = gps.get()

    if result:
        print(gps.parse(result))

    time.sleep(30)
