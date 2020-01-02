#/usr/bin/python
import time
import can


bus = can.interface.Bus(bustype='socketcan', channel='vcan0', bitrate=500000)

while True:
    # msg_recv = bus.recv(0.0)
    # print("Message sent on {}".format(bus.channel_info))
    for msg in bus:
    	print(msg)
