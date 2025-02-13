# StratoPi 🎈 👽 🛸

## Goal

The goal is to launch a latex weather balloon filled with helium into the stratosphere while recording the entire video footage of the ascent and descent flights using multiple cameras. Successfully recover the payload, which includes the Raspberry Pi computer, flight data _(date, GPS, temperature, pressure, humidity, etc)_, and video cameras and footage. If you like computing, Raspberry Pi's, space, flight, and have way too much free time, this might just be the project for you.

- Altitude goal is 100,000ft _(30,480m)_.

Open sourced and community developed. StratoPi is 100% purely a hobby project with zero financial incentives. All parts purchased at retail prices. My experience is mostly as the founder of [Elastic Byte](https://elasticbyte.net) and a DevOps Engineer so this is definitely uncharted territory for me personally.

## Parts

View the [parts list](https://github.com/stratopi-org/stratopi/blob/master/PARTS.md).

## Legality / FAA

According to the [Strato Flights website](https://www.stratoflights.com/en/tutorial/weather-balloon-registration-insurance/usa/#:~:text=To%20launch%20a%20weather%20balloon,FAA%20Part%20101), must have approval from the Federal Aviation Administration _(FAA)_. _Laws and regulations may undergo significant changes at any time due to ongoing developments involving spy balloons._

See:

- https://eclipse.montana.edu/education/engineering-course/eng-lesson09-faaregs.pdf
- https://www.ecfr.gov/current/title-14/chapter-I/subchapter-F/part-101
- https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-48
- https://www.cbsnews.com/news/military-tracking-balloon-western-us-military/

## Media

[![Raspberry Pi computer, battery, communications payload overview](http://img.youtube.com/vi/SpzycIWPKsQ/0.jpg)](http://www.youtube.com/watch?v=SpzycIWPKsQ "Raspberry Pi computer, battery, communications payload overview")

[![RunCam 5 Camera Unboxing](http://img.youtube.com/vi/Ua4CM7kJQfI/0.jpg)](http://www.youtube.com/watch?v=Ua4CM7kJQfI "RunCam 5 Camera Unboxing")

![RunCam 5 Camera Power Test](https://github.com/stratopi-org/stratopi/blob/master/media/images/camera_test.jpg)

## Software architecture

All the software is written in Python 3 using standard PyPI packages. The pattern of each application is essentially poll for some data, and then insert that data into PostgreSQL. The exception being the communication application which pulls data from PostgreSQL and sends it to Slack via wireless networks. Originally, I was planning to run each application in a Docker container but decided to keep things as simple as possible and opted to use tried and true _systemd_ services for each application. [KISS](https://en.wikipedia.org/wiki/KISS_principle)!

- ### [battery](https://github.com/stratopi-org/stratopi/tree/master/software/battery)

Polls the battery percentage as well as the battery temperature and inserts the data into PostgreSQL.

- ### [communication](https://github.com/stratopi-org/stratopi/tree/master/software/communication)

Pulls battery, environmental, and location data from PostgreSQL and inserts into Slack channels using wireless networks.

- ### [environmental](https://github.com/stratopi-org/stratopi/tree/master/software/environmental)

Polls the Bosch BME280 sensor, Raspberry Pi CPU temperature, and inserts the data into PostgreSQL. Provides temperature, atmospheric pressure, and humidity.

- ### [location](https://github.com/stratopi-org/stratopi/tree/master/software/location)

Polls the Waveshare GPS and inserts the data into PostgreSQL. Provides date, time, latitude, longitude, altitude, speed, and course. From course, can also determine direction such as North, Southeast, etc.

## Tests

View [various tests](https://github.com/stratopi-org/stratopi/blob/master/docs/tests.md) _(mass, power, etc)_.

## Wanna help?

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
