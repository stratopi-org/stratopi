# StratoPi

## Goals

Launch a weather balloon filled with helium into the stratosphere while recording the entire video footage of the ascent and descent flights using multiple cameras. Successfully recover the payload, which includes the Raspberry Pi computer, flight data, as well as the video cameras and footage.

## Parts

### Computer

[Raspberry Pi 3 B+](https://www.raspberrypi.com/products/raspberry-pi-3-model-b-plus/). I already had an extra Raspberry Pi 3 B+ lying around so I used that. It's plenty powerful in terms of processing and memory and it's really power efficient. A newer [Raspberry Pi 4](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) would work as well.

### Cellular communication / GPS

[Waveshare SIM7600A-H 4G HAT Board](https://www.amazon.com/gp/product/B07PLTP3M6). Provides GPS support which facilitates locating the payload after descent and communications capability using 4G wireless networking.

### Computer battery

[Pisugar 3 Plus](https://www.amazon.com/gp/product/B09MJ876FW). A polished and amazing integrated battery and software controller specifically designed for Raspberry Pi's.

### Temperature, pressure, humidity sensor

[Bosch BME280 Sensor](https://www.amazon.com/gp/product/B0BQFV883T). Provides environmental data; atmospheric pressure, temperature, and humidity.
I used the [ELEGOO 40pin cable pack](https://www.amazon.com/gp/product/B01EV70C78) to connect the BME280 sensor to the Raspberry Pi.

### Camera battery

[RGVOTA 38800mAh USB-A power bank](https://www.amazon.com/dp/B09H4GLZXT?th=1). Required extended battery power for the cameras.

## Software architecture

All the software is written in Python 3 using standard PyPI packages. Originally, I was planning to run each application in a Docker container but decided to keep things as simple as possible and opted to use tried and tested systemd services for each application. [KISS](https://en.wikipedia.org/wiki/KISS_principle)!

### battery

Polls the battery percentage as well as the battery tempature and inserts the data into PostgreSQL.

### communication

### environmental

Polls the Bosch BME280 sensor and inserts the data into PostgreSQL.

### location

Polls the Waveshare GPS and inserts the data into PostgreSQL. Provides date, time, latitude, longitude, altitude, speed, and course. From course, can also determine direction such as North, Southeast, etc.
