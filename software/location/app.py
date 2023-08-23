from lib import gps

gps.power_on()
print(gps.get_gps_position())
gps.power_off()
