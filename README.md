# StratoPi 🎈 👽 🛸

## Goal

The goal is to launch a latex weather balloon filled with helium into the stratosphere while recording the entire video footage of the ascent and descent flights using multiple cameras. Successfully recover the payload, which includes the Raspberry Pi computer, flight data _(date, GPS, temperature, pressure, humidity, etc)_, and video cameras and footage. If you like computing, Raspberry Pi's, space, flight, and have way too much free time, this might just be the project for you.

- Altitude goal is 100,000ft _(30,480m)_.

Open sourced and community developed. StratoPi is 100% purely a hobby project with zero financial incentives. All parts purchased at retail prices. Somewhat new/rookie to Python programming so go easy on me 😁. My experience is mostly as the founder of [Elastic Byte](https://elasticbyte.net) and a DevOps Engineer.

## Legality / FAA

According to the [Strato Flights website](https://www.stratoflights.com/en/tutorial/weather-balloon-registration-insurance/usa/#:~:text=To%20launch%20a%20weather%20balloon,FAA%20Part%20101), must have approval from the Federal Aviation Administration _(FAA)_. Current events related to spy balloons may change laws and regulations.

See:

- https://www.stratoflights.com/en/tutorial/weather-balloon-registration-insurance/usa/#:~:text=To%20launch%20a%20weather%20balloon,FAA%20Part%20101
- https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-48

## Videos

[![Raspberry Pi computer, battery, communications payload overview](http://img.youtube.com/vi/SpzycIWPKsQ/0.jpg)](http://www.youtube.com/watch?v=SpzycIWPKsQ "Raspberry Pi computer, battery, communications payload overview")

[![RunCam 5 Camera Unboxing](http://img.youtube.com/vi/Ua4CM7kJQfI/0.jpg)](http://www.youtube.com/watch?v=Ua4CM7kJQfI "RunCam 5 Camera Unboxing")

## Wanna Help?

- See [GitHub Issues](https://github.com/stratopi-org/stratopi/issues?q=is%3Aopen+is%3Aissue+label%3Aenhancement) for outstanding tasks
- Potentially joining the launch and recovery in person _(Tennessee launch...)_
- Code review and PR's of my _noob_ Python 🙈. Dig into the [software](https://github.com/stratopi-org/stratopi/tree/master/software).
- Parts recommendations and optimizations
- 3d modeling and printing _(structural and mounting aspects)_
- Website / Github Pages
- Flight, space, physics experience as I am sure I am negligently overlooking details
- GIS and GPS experience. KML, GeoJSON, GPS Visualizer, Google Earth/Maps
- Video editing of the flight footage 🤞
- Have a latex baloon "hookup"?
- Have a helium "hookup"? 😉

## Software architecture

All the software is written in Python 3 using standard PyPI packages. The pattern of each application is essentially poll for some data, and then insert that data into PostgreSQL. The exception being the communication application which pulls data from PostgreSQL and sends it via wireless networks. Originally, I was planning to run each application in a Docker container but decided to keep things as simple as possible and opted to use tried and true _systemd_ services for each application. [KISS](https://en.wikipedia.org/wiki/KISS_principle)!

- ### [battery](https://github.com/stratopi-org/stratopi/tree/master/software/battery)

Polls the battery percentage as well as the battery temperature and inserts the data into PostgreSQL.

- ### [communication](https://github.com/stratopi-org/stratopi/tree/master/software/communication)

- ### [environmental](https://github.com/stratopi-org/stratopi/tree/master/software/environmental)

Polls the Bosch BME280 sensor and inserts the data into PostgreSQL. Provides temperature, atmospheric pressure, and humidity.

- ### [location](https://github.com/stratopi-org/stratopi/tree/master/software/location)

Polls the Waveshare GPS and inserts the data into PostgreSQL. Provides date, time, latitude, longitude, altitude, speed, and course. From course, can also determine direction such as North, Southeast, etc.

## Parts

- #### Weather balloon

*(TBD)* [Latex weather balloon]()

- #### Computer

[Raspberry Pi 3 B+](https://www.raspberrypi.com/products/raspberry-pi-3-model-b-plus/). I already had an extra Raspberry Pi 3 B+ lying around so I used that. It's plenty powerful in terms of processing and memory and it's really power efficient. A newer [Raspberry Pi 4](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) would work as well.

- #### Cameras

[RunCam 5 Orange](https://shop.runcam.com/runcam-5-orange/). Ultra-light _(56 grams)_ 4K HD camera with image stabilization. Uses a Sony IMX 377 12MP sensor and specifically built for airborne [FPV](https://en.wikipedia.org/wiki/First-person_view_\(radio_control\)).<br />
[TEAMGROUP microSD Card 128GB - 3 Pack](https://www.amazon.com/dp/B09WRFQYW3). microSD storage for video footage.

- #### Cellular communication / GPS

[Waveshare SIM7600A-H 4G HAT Board](https://www.amazon.com/gp/product/B07PLTP3M6). Provides GPS support which facilitates locating the payload after descent and communications capability using 4G wireless networking.<br />
[Simbase SIM card and connectivity](https://www.simbase.com/). Provides wireless connectivity for IOT devices using multiple mobile operators. Wireless data is VERY expensive _($0.01 per MB)_ with Simbase so optimizations and clever solutions need to be implemented in the communications application.

- #### Auxiliary location

[Apple AirTag](https://www.apple.com/shop/buy-airtag/airtag/1-pack). Provides auxiliary location tracking using bluetooth and the Apple Find My network.

- #### Temperature, pressure, humidity sensor

[Bosch BME280 Sensor](https://www.amazon.com/gp/product/B0BQFV883T). Provides environmental data.
I used the [ELEGOO 40pin cable pack](https://www.amazon.com/gp/product/B01EV70C78) to connect the BME280 sensor to the Raspberry Pi.

- #### Computer battery

[PiSugar 3 Plus](https://www.amazon.com/gp/product/B09MJ876FW). A integrated battery and software controller specifically designed for Raspberry Pi's.

- #### Camera battery

[RGVOTA 38800mAh USB-A power bank](https://www.amazon.com/dp/B09H4GLZXT?th=1). Required extended battery power for the cameras.

- #### Parachute

*(TBD)* [Parachute]()<br />
*(TBD)* [Parachute cord]()

- #### Payload external shroud and miscellaneous

*(TBD)* [Styrofoam cooler]()<br />
*(TBD)* [Hand warmers]()
