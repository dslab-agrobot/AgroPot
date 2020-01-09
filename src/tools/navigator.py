#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Navigator to control robot to move and act
__copyright__="Jiangxt"
__email__ = "<jiangxt404@qq.com>"
__license__ = "GPL V3"
__version__ = "0.1"

"""
Project_PATH = "/home/pi/"
import can
import canMsgHandler
from os.path import join as pj
from multiprocessing import Process,JoinableQueue
import subprocess



class Navigator(object):
    
    CAN_SUV_FG = True	

    """
    Navigator to control the robot
    
    1) Suveillance of the can devices
    2)
    """
    def __init__(self):
        self.channel = "can0"
        self.can_daemon = canMsgHandler.CanMsgListener()
        self.can_daemon.start()
        self.bus = can.interface.Bus(bustype='socketcan', channel=self.channel, bitrate=500000)


    @staticmethod
    def turn_led(act: str, color: str):
        cmd = "%s_%s" % (act.lower(), color.lower())
        proc = subprocess.Popen(['sudo', 'python3', pj(Project_PATH, 'led.py'), 'on_r'])
        proc.wait()

    def move_slider(self, direction: str, distance: int):
        for sub_cmd in canMsgHandler.CANFunctionList.move(direction=direction, distance=distance):
            if self.can_daemon.is_alive():
                proc = subprocess.Popen(['cansend', 'can0', sub_cmd])
            else:
                raise ValueError("Can Daemon dead ! ")


def main():
    nav = Navigator()
    nav.move_slider("X", 50)


if __name__ == "__main__":
    main()

