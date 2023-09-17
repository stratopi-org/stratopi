# StratoPi 🌌 👽 🛸

## Goal

Launch a latex weather balloon filled with helium into the stratosphere while recording the entire video footage of the ascent and descent flights using multiple cameras. Successfully recover the payload, which includes the Raspberry Pi computer, flight data, and video cameras and footage.

- Altitude goal is 100,000ft _(30,480m)_.

StratoPi is 100% purely a hobby project with zero financial incentives. All parts purchased at retail prices. Somewhat new/rookie to Python programming so go easy on me 😃. My experience is mostly as a DevOps Engineer.

## Parts

- #### Weather balloon

[Latex weather balloon]()

- #### Computer

[Raspberry Pi 3 B+](https://www.raspberrypi.com/products/raspberry-pi-3-model-b-plus/). I already had an extra Raspberry Pi 3 B+ lying around so I used that. It's plenty powerful in terms of processing and memory and it's really power efficient. A newer [Raspberry Pi 4](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) would work as well.

- #### Cameras

[RunCam 5 Orange](https://shop.runcam.com/runcam-5-orange/). Ultra-light _(56 grams)_ 4K HD camera with image stabilization. Uses a Sony IMX 377 12MP sensor and specifically built for airborne [FPV](https://en.wikipedia.org/wiki/First-person_view_\(radio_control\)).

- #### Cellular communication / GPS

[Waveshare SIM7600A-H 4G HAT Board](https://www.amazon.com/gp/product/B07PLTP3M6). Provides GPS support which facilitates locating the payload after descent and communications capability using 4G wireless networking.

- #### Auxiliary location

[Apple AirTag](https://www.apple.com/shop/buy-airtag/airtag/1-pack). Provides auxiliary location tracking using bluetooth and the Apple Find My network.

- #### Temperature, pressure, humidity sensor

[Bosch BME280 Sensor](https://www.amazon.com/gp/product/B0BQFV883T). Provides environmental data; atmospheric pressure, temperature, and humidity.
I used the [ELEGOO 40pin cable pack](https://www.amazon.com/gp/product/B01EV70C78) to connect the BME280 sensor to the Raspberry Pi.

- #### Parachute

[Parachute]()<br />
[Parachute cord]()

- #### Payload external shroud and miscellaneous

[Styrofoam cooler]()<br />
[Hand warmers]()

- #### Computer battery

[Pisugar 3 Plus](https://www.amazon.com/gp/product/B09MJ876FW). A integrated battery and software controller specifically designed for Raspberry Pi's.

- #### Camera battery

[RGVOTA 38800mAh USB-A power bank](https://www.amazon.com/dp/B09H4GLZXT?th=1). Required extended battery power for the cameras.

## Software architecture

All the software is written in Python 3 using standard PyPI packages. Originally, I was planning to run each application in a Docker container but decided to keep things as simple as possible and opted to use tried and tested systemd services for each application. [KISS](https://en.wikipedia.org/wiki/KISS_principle)!

- ### [battery](https://github.com/stratopi-org/stratopi/tree/master/software/battery)

Polls the battery percentage as well as the battery tempature and inserts the data into PostgreSQL.

- ### [communication](https://github.com/stratopi-org/stratopi/tree/master/software/communication)

- ### [environmental](https://github.com/stratopi-org/stratopi/tree/master/software/environmental)

Polls the Bosch BME280 sensor and inserts the data into PostgreSQL.

- ### [location](https://github.com/stratopi-org/stratopi/tree/master/software/location)

Polls the Waveshare GPS and inserts the data into PostgreSQL. Provides date, time, latitude, longitude, altitude, speed, and course. From course, can also determine direction such as North, Southeast, etc.
