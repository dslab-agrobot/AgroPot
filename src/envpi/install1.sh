#!/bin/bash

# we have only one can-module in pi
sudo ip link set can0 type can bitrate 500000 restart-ms 100
sudo ifconfig can0 up

echo -e "allow-hotplug can0\niface can0 can static\n    bitrate 500000\n    restart-ms 100" | sudo tee -a /etc/network/interfaces

echo -e "dmesg | grep can\nsudo ip link add dev vcan0 type vcan\nsudo ip link set vcan0 up" | tee -a ~/.profile

echo -e "alias can_up='sudo ifconfig can0 up'\nalias can_down='sudo ifconfig can0 down'\nalias can_stat='sudo ip -details -statistics link show can0'\nalias vcan_setup='sudo modprobe vcan" | tee -a ~/.bashrc