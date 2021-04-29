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
import argparse
import random
from VSMD import *
import RPi.GPIO as GPIO
import os,sys
import can

from os.path import join as pj
import time
from multiprocessing import Process, Manager, Value
import subprocess

GPIO.setmode(GPIO.BMC)
PIN_PUMP = 4
PIN_LIGHT = 18
GPIO.setup([PIN_LIGHT, PIN_PUMP], GPIO.OUT)

pos = {"X1": 0, "X2": 0, "Y": 0, "Z": 0}
FLAG = False


class DeviceTable(Enum):
    """Device table for our project

            ..note:
                1. device = DeviceTable(id)  # get a enum
                2. id=DeviceTable.xxx.value  # get a string
            """
    # Target device only
    BroadCast = "000000000"
    SliderX1 = "000000001"
    SliderX2 = "000000010"
    SliderY = "000000011"
    SliderZ = "000000100"
    Pi = "000001111"
    UnKnow = "111111111"
    FUCK = "233333"


class Navigator(object):
    
    CAN_SUV_FG = True

    """
    Navigator to control the robot
    
    1) Suveillance of the can devices
    2)
    """
    class MotorsController(object):

        class CanMonitor(Process):
            def __init__(self, mc, bus, elements):
                super().__init__()
                self.mc = mc
                self.bus = bus
                self.elements = elements

            def run(self):
                for _msg in self.bus:

                    if self.mc.sync_dict["flag"]:
                        return
                    frame = VsmdCanFrame(_msg, debug=False)
                    device = str(frame.ext_frame.source_device).split(".")[-1]
                    if frame.ERROR_FLG:
                        debug_msg = frame.debug_msg
                        print(debug_msg)

                    if frame.data_frame.cw == CWTable.R_Stat_Reg:

                        regs_values = frame.data_frame.regs_values
                        status = frame.data_frame.status
                        sensors = frame.data_frame.sensors
                        keys = [x[0] for x in regs_values]
                        if "STATUS" in keys:
                            if device in ["SliderX1", "SliderX2"]:
                                if str(sensors[4][1]) == "0":
                                    self.mc.sync_dict["limit"]["X+"] = True
                                if str(sensors[5][1]) == "0":
                                    self.mc.sync_dict["limit"]["X-"] = True
                            elif device == "SliderY":
                                if str(sensors[4][1]) == "0":
                                    self.mc.sync_dict["limit"]["Y+"] = True
                                if str(sensors[5][1]) == "0":
                                    self.mc.sync_dict["limit"]["Y-"] = True
                            elif device == "SliderZ":
                                if str(sensors[4][1]) == "0":
                                    self.mc.sync_dict["limit"]["Z+"] = True
                                if str(sensors[5][1]) == "0":
                                    self.mc.sync_dict["limit"]["Z-"] = True
                        else:
                            print("%s : %s " % (frame.ext_frame.source_device, regs_values))

                            value = regs_values[0][1]
                            if device not in self.elements:
                                continue
                            if device == "SliderX1":
                                self.mc.sync_dict["X1"] = value
                            elif device == "SliderX2":
                                self.mc.sync_dict["X2"] = value
                            elif device == "SliderY":
                                self.mc.sync_dict["Y"] = value
                            elif device == "SliderZ":
                                self.mc.sync_dict["Z"] = value

        def __init__(self):

            self.can0 = can.interface.Bus(bustype='socketcan', channel="can0", bitrate=500000)
            self.can1 = can.interface.Bus(bustype='socketcan', channel="can1", bitrate=500000)
            self.can0_monitor = self.CanMonitor(self, self.can0, ["SliderX1", "SliderX2"])
            self.can1_monitor = self.CanMonitor(self, self.can1, ["SliderY", "SliderZ"])
            print("CAN buses initialized")
            self.manager = Manager()
            # X 45cm Y 49cm Z 49cm
            self.max = {"X1": 358937, "X2": 358697, "Y": 385720, "Z": 390497}
            self.mileage = {"X1": 0, "X2": 0, "Y": 0, "Z": 0}
            self.sync_dict = self.manager.dict({"X1": 0, "X2": 0, "Y": 0, "Z": 0, "flag": False,
                                                "limit": {"X+": False, "X-": False, "Y+": False, "Y-": False
                                                          , "Z+": False, "Z-": False}})
            self.can0.send(str2can_msg(CommonCMD.enable_motor("All")))
            self.can1.send(str2can_msg(CommonCMD.enable_motor("All")))
            print("CAN motors enabled")
            self.run()

        def __del__(self):
            print("Total mileage: ", self.mileage)
            self.can0.send(str2can_msg(CommonCMD.disable_motor("All")))
            self.can1.send(str2can_msg(CommonCMD.disable_motor("All")))
            print("CAN motors disabled")


        def run(self):
            self.can0_monitor.start()
            self.can1_monitor.start()
            print("Message daemon on")
        
        def terminate(self):
            self.can0_monitor.terminate()
            self.can1_monitor.terminate()

        def move(self, direction: str, distance, is_plus=False):

            direction = direction.upper()
            # 800 plus per mm, definition in VSMD
            if not is_plus:
                plus = int(distance*800)
            else:
                plus = int(distance)

            # 3 is a estimation of time gap between two moves
            sleep_time = abs(plus) / 6400.0 + 1
            print("Direction %s , plus %d, estimated time %.2f" % (direction, plus, sleep_time))
            if direction == "X":
                self.mileage["X1"] += plus
                self.mileage["X2"] += plus
                self.can0.send(str2can_msg(CommonCMD.move_dis("All", plus)))
                time.sleep(sleep_time)
                self.can0.send(str2can_msg(CommonCMD.read_status_regs("X1", StatusRegTable.POS, 1)))
                self.can0.send(str2can_msg(CommonCMD.read_status_regs("X2", StatusRegTable.POS, 1)))
            elif direction == "Y":
                self.mileage["Y"] += plus
                self.can1.send(str2can_msg(CommonCMD.move_dis("Y", plus)))
                time.sleep(sleep_time)
                self.can1.send(str2can_msg(CommonCMD.read_status_regs("Y", StatusRegTable.POS, 1)))
            elif direction == "Z":
                self.mileage["Z"] += plus
                self.can1.send(str2can_msg(CommonCMD.move_dis("Z", plus)))
                time.sleep(sleep_time)
                self.can1.send(str2can_msg(CommonCMD.read_status_regs("Z", StatusRegTable.POS, 1)))

            # print(self.mileage, self.sync_dict)
            time.sleep(0.1)
            self.can0_monitor.join(0.1)
            self.can1_monitor.join(0.1)

            print("Deviation X1:%d, X2:%d, Y:%d, Z:%d" %
                  (self.mileage["X1"] - self.sync_dict["X1"], self.mileage["X2"] - self.sync_dict["X2"],
                   self.mileage["Y"] - self.sync_dict["Y"], self.mileage["Z"] - self.sync_dict["Z"]))

        def config(self, device="All", CID=1, BDR=500000, MCS=5, SPD=6400.0, ACC=192000000.0, DEC=192000000.0,
                   CRA=1.6799999475479126, CRN=1.6799999475479126, CRH=0.8399999737739563,
                   MSR_MSV_PSR_PSV="05000600", PAE=0, CAF=1, EMOD=1):
            for cmd in [
                CommonCMD.write_data_regs(device, DataRegTable.CID, CID),
                CommonCMD.write_data_regs(device, DataRegTable.BDR, BDR),
                CommonCMD.write_data_regs(device, DataRegTable.MCS, MCS),
                CommonCMD.write_data_regs(device, DataRegTable.SPD, SPD),
                CommonCMD.write_data_regs(device, DataRegTable.ACC, ACC),
                CommonCMD.write_data_regs(device, DataRegTable.DEC, DEC),
                CommonCMD.write_data_regs(device, DataRegTable.CRA, CRA),
                CommonCMD.write_data_regs(device, DataRegTable.CRN, CRN),
                CommonCMD.write_data_regs(device, DataRegTable.CRH, CRH),
                CommonCMD.write_data_regs(device, DataRegTable.MSR_MSV_PSR_PSV, MSR_MSV_PSR_PSV),
                CommonCMD.write_data_regs(device, DataRegTable.PAE, PAE),
                CommonCMD.write_data_regs(device, DataRegTable.CAF, CAF),
                CommonCMD.write_data_regs(device, DataRegTable.EMOD, EMOD),
                CommonCMD.save(device)
            ]:
                # self.bus.send(str2can_msg(cmd))
                print(cmd)

        def zero_config(self, device="All", ZMD=4,OSV=1,SNR=4,ZSD=-1000,ZSP=1600):
            for cmd in [
                CommonCMD.write_data_regs(device, DataRegTable.ZMD, ZMD),
                CommonCMD.write_data_regs(device, DataRegTable.OSV, OSV),
                CommonCMD.write_data_regs(device, DataRegTable.SNR, SNR),
                CommonCMD.write_data_regs(device, DataRegTable.ZSD, ZSD),
                CommonCMD.write_data_regs(device, DataRegTable.ZSP, ZSP),
                CommonCMD.save(device)
            ]:
                self.can0.send(str2can_msg(cmd))
                self.can1.send(str2can_msg(cmd))
                time.sleep(0.2)
                # print(cmd)

        def zero(self, device="All"):
            if device == "All":
                self.can0.send(str2can_msg(CommonCMD.zero("All")))
                self.can1.send(str2can_msg(CommonCMD.zero("Y")))
                self.can1.send(str2can_msg(CommonCMD.zero("Z")))
            elif device == "X":
                self.can0.send(str2can_msg(CommonCMD.zero("X")))
            elif device == "All":
                self.can1.send(str2can_msg(CommonCMD.zero(device)))
            time.sleep(120)

        def random_move_test(self, max_trials=50000):

            for i in range(max_trials):
                # if self.sync_dict["flag"]:
                #     print("ERROR !!")
                #     return
                print("Random test %d in %d" % (i, max_trials))
                dirs = ("X", "Y", "Z")
                # direction = "X"
                direction = random.choice(dirs)
                rag = [0, 0]

                self.can0.send(str2can_msg(CommonCMD.read_status_regs("All", StatusRegTable.STATUS, 1)))
                time.sleep(0.1)
                self.can0_monitor.join(0.1)
                self.can1_monitor.join(0.1)

                if direction == "X":
                    x1_r = [800 - self.sync_dict["X1"], self.max["X1"] - self.sync_dict["X1"] - 800]
                    x2_r = [800 - self.sync_dict["X2"], self.max["X2"] - self.sync_dict["X2"] - 800]
                    rag[0] = x1_r[0] if x1_r[0] > x2_r[0] else x2_r[0]
                    rag[1] = x1_r[1] if x1_r[1] < x2_r[1] else x2_r[1]
                    # print(x1_r, x2_r, rag)
                    if self.sync_dict["limit"]["X+"]:
                        rag[1] = 0
                    if self.sync_dict["limit"]["X-"]:
                        rag[0] = 0
                elif direction in ["Y", "Z"]:
                    rag = [800 - self.sync_dict[direction], self.max[direction] - self.sync_dict[direction] - 800]
                    if self.sync_dict["limit"]["%s+" % direction]:
                        rag[1] = 0
                    if self.sync_dict["limit"]["%s-" % direction]:
                        rag[0] = 0
                print(rag)
                distance = random.randint(rag[0], rag[1])

                self.move(direction=direction, distance=distance, is_plus=True)

        def query(self):

            self.can0.send(str2can_msg(CommonCMD.read_status_regs("All", StatusRegTable.POS, 1)))
            self.can1.send(str2can_msg(CommonCMD.read_status_regs("All", StatusRegTable.POS, 1)))
            time.sleep(0.5)

    def __init__(self):
        self.motorsController = Navigator.MotorsController()

    @staticmethod
    def turn_led(act: str, color: str):
        cmd = "%s_%s" % (act.lower(), color.lower())
        proc = subprocess.Popen(['sudo', 'python3', pj(Project_PATH, 'led.py'), 'on_r'])
        proc.wait()

    @staticmethod
    def turn_pump(act: int):
        GPIO.output(PIN_PUMP, act)

    @staticmethod
    def turn_sun(act: int):
        GPIO.output(PIN_LIGHT, act)


    def move_slider(self, direction: str, distance: float):
        self.motorsController.move(direction=direction, distance=distance)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("act", help="action", type=str)
    parser.add_argument("--n", help="num", type=float)
    args = parser.parse_args()
    nav = Navigator()
    # return
    args.act = str(args.act).upper()
    if args.act in ['X', 'Y', 'Z']:
        if int(args.n) != 0:
            nav.move_slider(args.act, args.n)
        else:
            nav.motorsController.zero(args.act)
    elif args.act == 'T':
        nav.motorsController.random_move_test()
    elif args.act == 'C':
        nav.motorsController.config()
    elif args.act == 'Q':
        nav.motorsController.query()
    elif args.act == 'O':
        nav.motorsController.zero_config(device="All")
        nav.motorsController.zero(device="All")
    elif args.act == 'S':
        nav.turn_sun(int(args.n))
    elif args.act == 'P':
        nav.turn_pump(int(args.n))

    nav.motorsController.terminate()


if __name__ == "__main__":
    main()

