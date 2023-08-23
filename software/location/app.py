from lib import gps

gps.power_on()
gps.init()
print(gps.get_gps())
gps.power_off()
