#!/bin/bash

# shellcheck disable=SC2024
echo -e "dtparam=spi=on \n dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25,spimaxfrequency=1000000" | sudo tee -a /boot/config.txt

# can to communcate in can-net
sudo pip3 install python-can

# neopixel to controll led light
pip3 install rpi_ws281x adafruit-circuitpython-neopixel

# shell can test
sudo apt install can-utils

sudo reboot