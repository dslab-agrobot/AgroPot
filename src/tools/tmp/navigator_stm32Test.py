#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Navigator to control robot to move and act
__copyright__="Jiangxt"
__email__ = "<jiangxt404@qq.com>"
__license__ = "GPL V3"
__version__ = "0.1"

"""
import argparse
import os
from os.path import join as pj
import sys
import time
import pickle
import cv2
from multiprocessing import Manager, Process, Value
from detector import *
from canManager import *
from datetime import datetime as dt
import json
dir_path = os.path.dirname(os.path.realpath(__file__))

# from cobot import *

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
        os.system("usbreset")
        self.readStat()
        self.bus = can.interface.Bus(
            channel=self.stat["channel"], bustype='socketcan_ctypes', bitrate = self.stat["bitrate"])
        # bitrate = 500000
        self.bus.send(KinggoCAN.enable(DeviceID.motorBroadcastid))
        self.send(KinggoCAN.disable(DeviceID.motorBroadcastid))
        # self.mycobot = RobotArm()


        time.sleep(0.5)
        self.maxmium= {
            "F":12000,
            "X":450,
            "Y":700,
            "Z":350
        }
        # zeroing
        # WheelWard X Y Z
        # self.stat = {}
        
        print("机器人前后移动 F 零点:医校")
        print("云台前后移动 X 零点: 医校")
        print("云台水平移动 Y 零点: 体育馆")
        print("云台垂直移动 Z 零点: 下")
        print(self.stat)
        if self.stat["next_dir"] == -1:
            print("机器人自动任务下次前进方向 医校")
        elif self.stat["next_dir"] == 1:
            print("机器人自动任务下次前进方向 操场")
           
    
    def __del__(self):
        self.saveStat()

        
    def saveStat(self):
        return
        _f = open(pj(dir_path,'robot.json'), 'w')
        json.dump(self.stat, _f)
        _f.close()

    def readStat(self):

        if os.path.exists(pj(dir_path,'robot.json')):
            _f = open(pj(dir_path,'robot.json'), 'r')
            self.stat = json.load(_f)
            _f.close()
        else:
            print('no robot.json file found !') 
            self.stat = {
                "next_dir": -1,
            }
            self.saveStat()
             

    def data_collection(self):
        # distance_f = 10000  # 10 m, 1000 mm: 1m
        data_dir = os.path.join(
            "/home/pi/data",  dt.now().strftime("%Y%m%d-%H%M"))
        
        
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        step_f = 320
        step_times = 32
        step_dir = self.stat["next_dir"]
        for i in range(step_times):
            img = camera_capture()
            img_path = os.path.join(
                data_dir,  "%03d.png" % i)
            cv2.imwrite(img_path, img)
            self.move(GroupID.groupWheel, step_f * step_dir)
        self.stat["next_dir"] = step_dir*-1
        self.saveStat()
        
    def data_collection_fakeTest(self):
            # distance_f = 10000  # 10 m, 1000 mm: 1m
        step_dir = -1
        for t in range(1,10000):
            step_f = 320
            step_times = 32
            # step_dir = self.stat["next_dir"]
            for i in range(step_times):
                self.move(GroupID.groupWheel, step_f * step_dir)
            step_dir = step_dir*-1
            # self.stat["next_dir"] = step_dir*-1
            # self.saveStat()

    def send(self, msg, st=0.1):
        self.bus.send(msg)
        time.sleep(st)
        pass

    def move(self, device: Enum, value_mm, sleep=True):
        def soft_limit():
            if device == GroupID.groupWheel:
                _v = self.stat["F"] + value_mm
                if _v < 0 or _v > self.maxmium["F"]:
                    return False
                else:
                    self.stat["F"] = _v
            elif device == GroupID.groupSlider:
                _v = self.stat["X"] + value_mm 
                if _v < 0 or _v > self.maxmium["X"]:
                    return False
                else:
                    self.stat["X"] = _v
            elif device == DeviceID.motorSlideY1:
                _v = self.stat["Y"] + value_mm 
                if _v < 0 or _v > self.maxmium["Y"]:
                    return False
                else:
                    self.stat["Y"] = _v
            elif device == DeviceID.motorSlideZ1:
                _v = self.stat["Z"] + value_mm 
                if _v < 0 or _v > self.maxmium["Z"]:
                    return False
                else:
                    self.stat["Z"] = _v
            else:
                raise Exception("Device ID not in safe range")
            return True
        
        if not soft_limit():
            print("[warning]: %s move out of range %d" % (device,value_mm))
            return
    
        
        time_slot = abs(value_mm/spd) 
        value_mm = int(value_mm * ppmm)
        # print("ppmm", ppmm)
        self.send(KinggoCAN.disable(DeviceID.motorBroadcastid))
        
        
        
        if device == GroupID.groupWheel:
            value_mm = value_mm // 4
            time_slot = time_slot / 4
            self.send(KinggoCAN.enable(DeviceID.motorWheelBackL))
            self.send(KinggoCAN.enable(DeviceID.motorWheelBackR))
            self.send(KinggoCAN.enable(DeviceID.motorWheelFrontL))
            self.send(KinggoCAN.enable(DeviceID.motorWheelFrontR))
            msg = KinggoCAN.pps_grp(device, value_mm)
        elif device == GroupID.groupSlider:
            self.send(KinggoCAN.enable(DeviceID.motorSlideX1))
            self.send(KinggoCAN.enable(DeviceID.motorSlideX2))
            msg = KinggoCAN.pps_grp(device, value_mm)
        elif device == DeviceID.motorSlideY1:
            self.send(KinggoCAN.enable(DeviceID.motorSlideY1))
            msg = KinggoCAN.move_to(device, value_mm)
        elif device == DeviceID.motorSlideZ1:
            self.send(KinggoCAN.enable(DeviceID.motorSlideZ1))
            msg = KinggoCAN.move_to(device, value_mm)
        else:
            raise Exception("Device ID not in safe range")

        # if device in [GroupID.groupWheel, GroupID.groupSlider]:
        #     msg = KinggoCAN.pps_grp(device, value_mm)
        # elif device in [DeviceID.motorSlideY1, DeviceID.motorSlideZ1]:
        #     msg = KinggoCAN.move_to(device, value_mm)
        # else:
        #     raise Ex
        # ception("Device ID not in safe range")
        self.send(msg)
        time_slot += 0.75
        print("Waiting for moving: %.2f" % time_slot)
        
        self.saveStat()
        if sleep:
            time.sleep(time_slot)

    def test(self,idx):
        img = camera_capture()
        height, width, channels = img.shape
        img = cv2.line(img, (0,height//2), (width,height//2), (0,255,0), 2)
        img = cv2.line(img, (width//2,0), (width//2,height), (0,255,0), 2)
        cv2.imwrite("t%02d.png"%idx, img)
        return
        self.move(GroupID.groupWheel, -100, False)
        for i in range(1):
            img = camera_capture()
            cv2.imwrite("move%d.png"%i, img)
            time.sleep(0.25)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("act", help="action", type=str)
    parser.add_argument("--n", help="num, mm for move", type=float)
    args = parser.parse_args()
    nav = Navigator()
    # listener = CanMsgListener(channel=nav.stat["channel"],bitrate=nav.stat["bitrate"],loglevel= KinggoCAN.LogLevel.stm32_fail_only)
    listener = CanMsgListener(channel=nav.stat["channel"],bitrate=nav.stat["bitrate"],loglevel= KinggoCAN.LogLevel.all)
    listener.start()
    
    args.act = str(args.act).upper()
    if args.act == "F":
        nav.move(GroupID.groupWheel, args.n)
    elif args.act == "X":
        nav.move(GroupID.groupSlider, args.n)
    elif args.act == "Y":
        nav.move(DeviceID.motorSlideY1, args.n)
    elif args.act == "Z":
        nav.move(DeviceID.motorSlideZ1, args.n)
    elif args.act == "T":
        nav.test(args.n)
    elif args.act == "D":
        nav.data_collection()
    elif args.act == "FT":
        nav.data_collection_fakeTest()
    # elif args.act == "A":
    #     # animation()
    #     pass
    
    listener.terminate()
    listener.join()



if __name__ == "__main__":
    main()

# python3 navigator.py X --n 1
