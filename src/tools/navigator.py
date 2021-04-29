#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Navigator to control robot to move and act
__copyright__="Jiangxt"
__email__ = "<jiangxt404@qq.com>"
__license__ = "GPL V3"
__version__ = "0.1"

"""
import os
import argparse
from multiprocessing import Process, Manager, Value
import time
import sys
from cobot import *
from canManager import *

# Speed of motor for plus
# Unit : plus pre second
spd_p = 6400

# speed for motor
# Unit : mm/s
# spd = (p_pmm * send_spacing / 1000ms/s)^-1
spd = spd_p/ppa*mpa

SafeDevice = [
    GroupID.groupSlider,
    GroupID.groupWheel,
    DeviceID.motorSlideY1,
    DeviceID.motorSlideZ1
]


class Navigator(object):
    def __init__(self):
        self.bus = can.interface.Bus(channel='can0', bustype='socketcan_ctypes')  # socketcan_native
        # # bitrate = 500000
        # self.bus.send(KinggoCAN.enable(DeviceID.motorBroadcastid))

        # zeroing
        # WheelWard X Y Z
        self.pos = [0, 0, 0, 0]
        pass

    def move(self, device: Enum, value_mm):
        time_slot = value_mm/spd + 0.75
        value_mm = int(value_mm)
        if device in [GroupID.groupWheel, GroupID.groupSlider]:
            msg = KinggoCAN.pps_grp(device.value, value_mm)
        elif device in [DeviceID.motorSlideY1, DeviceID.motorSlideZ1]:
            msg = KinggoCAN.move_to(device.value, value_mm)
        else:
            raise Exception("Device ID not in safe range")
        self.bus.send(msg)
        print("Waiting for moving: %.2f" % time_slot)
        time.sleep(time_slot)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("act", help="action", type=str)
    parser.add_argument("--n", help="num", type=float)
    args = parser.parse_args()
    nav = Navigator()

    args.act = str(args.act).upper()
    if args.act == "F":
        nav.move(GroupID.groupWheel, args.n)
    elif args.act == "X":
        nav.move(GroupID.groupSlider, args.n)
    elif args.act == "Y":
        nav.move(DeviceID.motorSlideY1, args.n)
    elif args.act == "Z":
        nav.move(DeviceID.motorSlideZ1, args.n)
    elif args.act == "A":
        animation()
        pass



if __name__ == "__main__":
    main()
