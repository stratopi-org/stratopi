import sys
import signal
import time
import pprint
from lib import gps

signal.signal(signal.SIGINT, lambda sig, frame: (gps.power_off(), sys.exit(0)))
gps.power_on()

while True:
    result = gps.get()

    if result:
        pprint(gps.parse(result))

    time.sleep(30)
