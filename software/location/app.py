from lib import gps

gps.power_on()
print(gps.get_gps())
gps.power_off()
