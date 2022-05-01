import os
import can
import time
import sys
from enum import Enum
from typing import Union
from ctypes import *
# from VSMD.canMsgHandler import VsmdCanFrame

# plus base for motor
step_base = 200

# plus msc for motor
step_mcs = 32

# plus per around
# The motor has ppc plus to rotate a complete around
ppa = step_base * step_mcs

# millimeter per around
mpa = 8

# plus per mm
ppmm = ppa/mpa

# Speed of motor for plus
# Unit : plus pre second
spd_p = 19200

# speed for motor
# Unit : mm/s
# spd = (p_pmm * send_spacing / 1000ms/s)^-1
spd = spd_p/ppa*mpa


def hex2float(_hex):
    # todo check
    i = int(_hex, 16)  # convert from hex to a Python int
    cp = pointer(c_int16(i))  # make this into a c integer
    fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
    return fp.contents.value


def float2hexlist(_f: float):
    cp = pointer(c_float(_f))
    fp = cast(cp, POINTER(c_int))
    if _f >= 0:
        res = hex(fp.contents.value)[2:].rjust(8, "0")
    else:
        res = hex(int(fp.contents.value) & 0xFFFFFFFF)[2:].rjust(8, "0")
    res = [int(res[i:i + 2], base=16) for i in range(0, len(res), 2)]
    return res


def int2hexlist(_i):
    # todo check
    if type(_i) == str:
        _i = int(_i)

    if _i >= 0:
        res = hex(_i)[2:].rjust(8, "0")
    else:
        res = hex(_i & 0xFFFFFFFF)[2:].rjust(8, "0")
    res = [int(res[i:i+2], base=16) for i in range(0, len(res), 2)]
    return res


def hex2int32(_hex):
    i = int(_hex, 16)
    cp = pointer(c_int(i))
    fp = cast(cp, POINTER(c_int16))
    return fp.contents.value


class DeviceID(Enum):
    motorBroadcastid = 0x00
    motorSlideX1 = 0x01
    motorSlideX2 = 0x02
    motorSlideY1 = 0x03
    motorSlideZ1 = 0x04
    motorWheelFrontL = 0x05
    motorWheelFrontR = 0x06
    motorWheelBackL = 0x07
    motorWheelBackR = 0x08


class GroupID(Enum):
    groupSlider = 0x01
    groupWheel = 0x05


class KinggoCANDebugger(object):

    def __init__(self, message, debug=False):
        """Decode raw message and send them to sub-frame

        :param message: message in socket can bus
        :param debug: print some log in decoding message

        .. note:
            This class write for CAN2.0 , which has 29-bitwise-ExtendId
            and 8-bytes-dataFrame

        .. note:
            DO NOT try to use para in protect level (like: _extID) if you
            have no idea what you are really doing with CAN Frame

        """

        # can device : can0 , vcan0
        self.channel = message.channel
        self.ERROR_FLG = False

        # Data Length Code , Every two 0x para get 1 DLC
        self.dlc = message.dlc

        # print(type(message.arbitration_id))
        if type(message.arbitration_id) == str:
            message.arbitration_id = int(message.arbitration_id, 16)

        # :type message.arbitration_id : int
        # Convert this int to bin and use string to storage
        ext_msg = str(bin(message.arbitration_id))[2:].rjust(29, "0")

        # :type [str,]
        if ext_msg[24] == "1":
            self.ERROR_FLG = True

        # :type message.data : bytearray
        # Each element convert to an int in bytearray iteration
        for t_hex in message.data:
            if hex(t_hex) != 0x1f:
                self.ERROR_FLG = False


class KinggoCAN(object):

    class MsgHead(Enum):
        """
        The first element of CAN msg
        bit 19 to bit 16
        """

        camera = 0x1 << 16
        motor = 0x2 << 16
        gpio = 0x3 << 16

    class MsgCustom(object):
        """
        The second element of CAN msg
        bit 15 to bit 8
        """

        @staticmethod
        def motor(current_index=1, total_index=1):
            return current_index << 12 | total_index << 8

    class MsgCmdVSMD(Enum):
        """
        The third element of CAN msg
        bit 7 to bit 0
        """

        enable = 0x01
        disable = 0x02
        original = 0x03
        stop = 0x04
        move = 0x05  # float
        move_to = 0x06  # int
        save = 0x07
        zero_start = 0x09
        relative_move = 0x0b  # int
        read_status_reg = 0x1e
        read_data_reg = 0x1f
        write_data_reg = 0x20
        pre_order_set = 0x0c  # int, move to
        pre_order_run = 0x21  # 0
        pre_order_group = 0x22  # int, move to

    @staticmethod
    def __cmd_generate(command_head: MsgHead, custom_word: int, command_body: Enum, data: list):
        msg = None
        idx = command_head.value | custom_word | command_body.value
        if command_head == KinggoCAN.MsgHead.motor:
            idx |= KinggoCAN.MsgCustom.motor()
            msgCmdVSMD = KinggoCAN.MsgCmdVSMD
            """
            handle VSMD motors (4 wheel and 3 slider)
            """
            data_frame = None
            if command_body in [msgCmdVSMD.enable, msgCmdVSMD.disable, msgCmdVSMD.stop, msgCmdVSMD.original,
                                msgCmdVSMD.zero_start, msgCmdVSMD.save, msgCmdVSMD.pre_order_run]:
                data_frame = [data[0].value, 0, 0, 0, 0, 0, 0, 0]
            elif command_body in [msgCmdVSMD.move]:
                d_list = float2hexlist(data[1])
                data_frame = [data[0].value, 0, 0, 0, d_list[0], d_list[1], d_list[2], d_list[3]]
            elif command_body in [msgCmdVSMD.move_to, msgCmdVSMD.relative_move,
                                  msgCmdVSMD.pre_order_set, msgCmdVSMD.pre_order_group]:
                d_list = int2hexlist(data[1])
                data_frame = [data[0].value, 0, 0, 0, d_list[0], d_list[1], d_list[2], d_list[3]]
            elif command_body in [msgCmdVSMD.read_status_reg, msgCmdVSMD.read_data_reg]:
                data_frame = [data[0].value, 0, 0, 0, data[1], data[2], 0, 0]
            # print("idx", idx, "data", data_frame)
            msg = can.Message(arbitration_id=idx, data=data_frame, extended_id=True)
        return msg

    @staticmethod
    def enable(target_id):
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.enable, data=[target_id])

    @staticmethod
    def disable(target_id):
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.disable, data=[target_id])

    @staticmethod
    def move(target_id, speed: float):
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.move, data=[target_id, speed])

    @staticmethod
    def stop(target_id):
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.stop, data=[target_id])

    @staticmethod
    def org(target_id):
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.original, data=[target_id])

    @staticmethod
    def zero_start(target_id):
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.zero_start, data=[target_id])

    @staticmethod
    def save(target_id):
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.save, data=[target_id])

    @staticmethod
    def move_to(target_id, pos: int):
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.move_to, data=[target_id, pos])

    @staticmethod
    def rmv(target_id, pos: int):
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.relative_move, data=[target_id, pos])

    @staticmethod
    def pps_set(target_id, pps: int):
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.pre_order_set, data=[target_id, pps])

    @staticmethod
    def pps_run(target_id):
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.pre_order_run, data=[target_id])

    @staticmethod
    def pps_grp(target_id, pps: int):
        # todo relative move
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.pre_order_group, data=[target_id, pps])

    @staticmethod
    def read_data_reg(target_id, addr: int, cnt: int):
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.read_data_reg, data=[target_id, addr, cnt])

    @staticmethod
    def read_stat_reg(target_id, addr: int, cnt: int):
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.read_status_reg, data=[target_id, addr, cnt])

    @staticmethod
    def write_data_reg(target_id, addr: int, value: int):
        # todo check type value
        return KinggoCAN.__cmd_generate(command_head=KinggoCAN.MsgHead.motor, custom_word=KinggoCAN.MsgCustom.motor(),
                                        command_body=KinggoCAN.MsgCmdVSMD.write_data_reg, data=[target_id, addr, value])

    @staticmethod
    def convert_msg2str(msg: can.Message):
        pass


motor = 0x2


def enableMotor(targetid):
    id = 0b00
    print(bin(id))
    id |= motor << 16
    # 第几帧
    id |= 1 << 12
    # 共几帧
    id |= 1 << 8
    # 指令代码
    id |= 0x01
    dataTx = [targetid, 0, 0, 0, 0, 0, 0, 0]
    print(hex(id), dataTx)
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    time.sleep(0.1)


# enableMotor(0x01)
# print(int2hexlist(-6401))
# print(hex(230))
# print(hex2float("ffe6ff"))
# print(hex2int32("004000"))
# print(bin(0<<7), int("0b1111",base=2))
