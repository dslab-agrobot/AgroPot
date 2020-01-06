from enum import IntEnum, Enum
from collections import OrderedDict
from ctypes import *
    #pointer, cast, c_int, c_float, POINTER
from types import MappingProxyType, DynamicClassAttribute


step_base = 200
mm_per_loop = 8


class AwesomeOrderedDict(OrderedDict):
    """ OrderedDict With Next() and First()

    Due to the data-format of DataFrame in RW register,
    we can access register with a start ADR with frames

    With Next() we can get next ADR of Register

    ..note::
        I can not access __map of OrderedDict that I use
        keys() to fix.

    """

    def __init__(self, *a, **kw):
        """
        No explict init will cause no keys
        :param a:
        :param kw:
        """
        super().__init__(*a, **kw)
        self.__list = list(self.keys())
        self.name_key = {}
        for _k, _v in self.items():
            self.name_key[_v[0]] = _k

    def next_key(self, key):
        """Get next key in order

        :param key:
        :return:
        :raise ValueError :
            when we get a last key or the key is not in the dict
        """
        __index = self.__list.index(key)
        if __index >= self.__list.__len__() - 1:
            raise ValueError("{!r} is the last key".format(key))
        __next = self.__list[__index + 1]
        return __next

    def get_key(self, t_name):
        return self.name_key[t_name]

    def first_key(self):
        for key in self:
            return key
        raise ValueError("OrderedDict() is empty")


class OhEnum(Enum):

    def p(self):
        if hasattr(self, "a"):
            print("Fuck")
        print(MappingProxyType(self._member_map_))
        print(self.value)
        pass

    @classmethod
    def t(cls):
        print(cls.__members__)

class Test(OhEnum):
    X = 1
    A = 2
    Y = 0
    Z = 3

a = Test.X
a.p()



class ExtIdTable(IntEnum):
    """Name of bits and their description

    xxx_id_0 and xxx_id_1 are used for slice of array
    like ">>> array[start:end] "

    """
    # Fixed value 0
    BIT27 = 0

    # Start of device ID for target
    # All zero (total 9) for broadcast
    target_id_0 = 1

    # End of device ID for target
    target_id_1 = 10

    # Fixed value 0
    BIT18 = 10

    # Start of device ID for source
    source_id_0 = 11

    # End of device ID for source
    source_id_1 = 20

    # Command word
    C0 = 20

    # Command word
    C1 = 21

    # Command or Address for register
    CMD0REG_0 = 22


class DeviceTable(Enum):
            """Device table for our project

            ..note:
                1. device = DeviceTable(id)  # get a enum
                2. id=DeviceTable.xxx.value  # get a string
            """
            # Target device only
            BroadCast = "000000000"
            SliderX0 = "000000001"
            SliderX1 = "000000010"
            SliderY = "000000011"
            SliderZ = "000000101"
            Pi = "000000110"


StatusValueTuple = (
    # Name index  Description         value 0      value 1
    (0, "S1", "Status of Sensor 1", "low level", "high level"),
    (1, "S2", "Status of Sensor 2", "low level", "high level"),
    (2, "S3", "Status of Sensor 3", "low level", "high level"),
    (3, "S4", "Status of Sensor 4", "low level", "high level"),
    (4, "POS", "Cur Pos Equals Tar Pos", "Not Equal", "Equal"),
    (5, "SPD", "Cur SPD Equals Tar SPD", "Not Equal", "Equal"),
    (6, "FLT", "Hard ware Error (Need Reset)", "Normal", "Error"),
    (7, "ORG", "Flag of origin", "Not at origin", "At origin"),
    (8, "STP", "Flag of stop", "Not stop (running)", "Stopped"),
    (9, "CMD_WRG", "Command Error (or Para out or range)", "CMD ok", "CMD Error"),
    (10, "FLASH_ERR", "Flash Error(RW in Flash)", "Normal", "Error"),  # reading or writing Flash
    (11, "ACTION", "Flag of offline action", "No offline action", "Offline action"),
    (13, "PWR", "Flag or motor enable energy", "ENA", "OFF"),
    (14, "ZERO", "Flag of end of the zeroing", "No zeroing/during zeroing", "zeroing end"),
    (15, "S5", "Status of Sensor 5", "low level", "high level"),
    (16, "S6", "Status of Sensor 6", "low level", "high level"),
    (20, "OTS", "Over heat", "normal", "Over heating protection"),
    (21, "OCP", "Over current", "normal", "Over current protection"),
    (22, "UV", "Under Voltage", "normal", "Under voltage protection"),
    (24, "ENC_ERR", "Encoding error(stall or encoder-error )", "normal", "error")
)

DigitRegDict = AwesomeOrderedDict({

    # ADR        Description   Value and Detail
    "0000000": ["Channel ID", "Determined by motor"],  # 0x00
    "0000001": ["Baud Rate", "Default 132000"],  # 0x01
    "0000010": ["Motor Control Subdivision",
                "0 : one step \n1 : 1/2\n2 : 1/4\n3 : 1/8\n4: 1/16\n5 : 1/32\n"
                "6 : 1/64 (Ser-045,13X,14X Only)\n7:1/128 (Ser-045,13X,14X Only)\n"
                "8 : 1/256 (Ser-045,13X,14X Only)"],  # 0x02
    "0000011": ["Target Speed", "(-192000,192000)pps"],  # 0x03
    "0000100": ["Accelerate", "(0,192000000)pps/s"],  # 0x04
    "0000101": ["Decelerate", "(0,192000000)pps/s"],  # 0x05
    "0000110": ["Current Accelerate", "0-2.5A(Series-025)\n0-4.5A(Series-045)"],  # 0x06
    "0000111": ["Current Normal", "0-2.5A(Series-025)\n0-4.5A(Series-045)"],  # 0x07
    "0001000": ["Current Hold", "0-2.5A(Series-025)\n0-4.5A(Series-045)"],  # 0x08
    "0001001": ["Function Settings for S1,S2", "See SensorValueTable"],  # 0x09
    "0001010": ["Function Settings for S3,S4", "See SensorValueTable"],  # 0x0A
    "0001011": ["Function Settings for S5,S6", "See SensorValueTable"],  # 0x0B
    "0001100": ["Reserved", "Blank"],  # 0x0C
    "0001101": ["Settings for S1-S6",
                "0 : Input\n1:Output\nBit Definition\nBIT0 : Fixed Input for S1\nBIT1 : Fixed Input for S2\n"
                "BIT2 : S3\nBIT3 : S4\nBIT4 : S5\nBIT5 : S6"],  # 0x0D
    "0001110": ["Zeroing mode definition",
                "0 : Zeroing off\n1 : Zeroing once\n2 : zeroing once + safe position\n3 : Double zeroing\n"
                "4 : Double zeroing + safe position\n5 : Non-sense zeroing (Series-136/146)"],  # 0x0E
    "0001111": ["Open zeroing Sensor level", "0 : low level\n1 : high level"],  # 0x0F
    "0010000": ["Sensor Number of zeroing", "0 : S1\n1 : S2\n2 : S3\n3 : S4\n4 : S5\n5 : S6"],  # 0x10
    "0010001": ["Zeroing's Speed", "Not Defined"],  # 0x11
    "0010010": ["Zeroing's Safe-Position", "Not Defined"],  # 0x12
    "0010011": ["Offline Mod", "0 : Normal mode\n1 : zeroing before offline"],  # 0x13
    "0010100": ["Duration when online and no communication",
                "0 : No auto running\n1-60 : time(sec)"],  # 0x14
    "0010101": ["Reserved", "Blank"],  # 0x15
    "0010110": ["Reserved", "Blank"],  # 0x16
    "0010111": ["MSR_MSV_PSR_PSV",
                        "MSR (Negative sensor)\n0 : No negative limit\n1 : S1\n2 : S2\n3 :S3\n4 : S4"
                        "5 : S5\n6 : S6\nMSV (Negative trigger level)\n0 : low level\n1 : high level\n"
                        "PSR (Positive Sensor)\n0 : 1 No positive\n1 : S1\n2 : S2\n3 : S3\n4 : S4\n5 : S5\n"
                        "6 : S6\nPSV (Positive trigger level)\n0 : 1 low level\n1 : high level"],  # 0x17
    "0011000": ["Power-on Attach Enable-energy", "0 : No auto ENA\n1 : Auto ENA"],  # 0x18
    "0011001": ["Command Attach FAQ.", "0 : Not support\n1 : Support"],  # 0x19
    "0011010": ["Zeroing After Power-on", "0 : No zeroing", "1: zeroing"],  # 0x1A
    "0011011": ["subdivision of Non-sense zeroing", "Not defined"],  # 0x1B
    "0011100": ["Current when Non-sense zeroing"],  # 0x1C
    "0100000": ["Encoding Mod", "Encoding Mod Off", "Encoding Mod On"]  # 0x20
})

StatusRegDict = AwesomeOrderedDict({
    "0000000": ["SPD", "Current Speed (float32)"],
    "0000001": ["POS", "Current Position (int32)"],
    "0000010": ["STATUS", "Status Code (u-int32)"],
    "0001010": ["VSMD_Version", "VSMD116-025T-1.0.000.171010"]
})


class SensorValueTable(IntEnum):
    no_action = 0
    origin_reset = 1
    stop_with_decelerate = 2
    stopWD_oriReset = 3
    stop_immediately = 4
    stopIm_oriReset = 5
    move_continuous_positive = 6
    move_continuous_negative = 7
    enable_offline = 8
    disable_offline = 9


class CMDTable(Enum):
    ENA = "0000001"
    OFF = "0000010"
    ORG = "0000011"
    STP = "0000100"
    MOV = "0000101"
    POS = "0000110"
    SAV = "0000111"
    OUTPUT = "0001000"
    ZERO_START = "0001001"
    ZERO_STOP = "0001010"
    RMV = "0001011"
    ACTION_START = "0010000"
    ACTION_STOP = "0010001"
    ACTION_CLEAR = "0010010"
    ACTION_ZERO = "0010011"
    ACTION_SPEED = "0010100"
    ACTION_POSITION = "0010101"
    ACTION_DELAY = "0010110"
    ENC = "0011101"
    READ_STATUS_REGS = "0011110"
    READ_DATA_REGS = "0011111"


class CWTable(Enum):
    R_Stat_Reg = "00"  # "Read Status Register"
    R_Data_Reg = "01"  # "Read Data Register"
    W_Data_Reg = "10"  # "Write Data Register"
    CMD = "11"  # "Command"


class BaudRateTable(Enum):
    BDR_001C2132 = 20000
    BDR_00168132 = 25000
    BDR_0012C132 = 30000
    BDR_000E1132 = 40000
    BDR_0000B413 = 50000
    BDR_00005A16 = 60000
    BDR_00007813 = 75000
    BDR_00004B15 = 80000
    BDR_00004B14 = 90000
    BDR_00005A13 = 100000
    BDR_00004813 = 125000
    BDR_00003C13 = 150000
    BDR_00002D13 = 200000
    BDR_00002413 = 250000
    BDR_00001E13 = 300000
    BDR_0000F153 = 400000
    BDR_00012132 = 500000
    BDR_00009163 = 600000
    BDR_00008153 = 750000
    BDR_00006163 = 900000
    BDR_00009132 = 1000000


def hex2float(_hex):
    i = int(_hex, 16)                   # convert from hex to a Python int
    cp = pointer(c_int(i))           # make this into a c integer
    fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
    return fp.contents.value

def float2hex(_f):
    cp = pointer(c_float(_f))
    fp = cast(cp, POINTER(c_int))
    return hex(fp.contents.value)

def hex2int32(_hex):
    i = int(_hex, 16)
    cp = pointer(c_int(i))
    fp = cast(cp, POINTER(c_int32))
    return fp.contents.value


class CommonCMD(object):

    @staticmethod
    def easy_cmd(tar: DeviceTable, src: DeviceTable, cw: CWTable, cmd0reg, data):
        """

        :param tar:
        :param src:
        :param cw:
        :param cmd0reg:
            1. R/W Register: RegName (str) like "Channel ID"
            2. Command to VSMD: Command (CMTable) like CMDTable.READ_DAtA_REGS
        :param data:
            1. Read Register: RegCount (int) like 3 which will be convert to D1 D2
            2. Write Register: Data (int or float) which will be convert to D1-D4 (Write one register per can-frame)
            3. Command: "STP,MOV,POS,RMV,READ_STATUS_REGS,READ_DATA_REGS" has data
        :return:
        """

        data_frame = "0"*16
        if cw == CWTable.R_Stat_Reg or cw == CWTable.R_Data_Reg :
            # It wrote in motor
            print("it determined by motor !")
            return "00000000#0000000000000000"
        if cw == CWTable.W_Data_Reg:
            reg_name = cmd0reg
            cmd0reg = DigitRegDict.get_key(cmd0reg)
            if reg_name in ["Target Speed", "Accelerate", "Decelerate", "Current Accelerate",
                            "Current Normal", "Current Hold"]:
                data_frame = str(float2hex(data))[2:].ljust(16, "0")
            elif reg_name in ["Channel ID", "Motor Control Subdivision"] :
                data_frame = str(hex(data))[2:].ljust(16, "0")
            else:
                print("Not Defined ! ")
                data_frame = str(hex(data))[2:].ljust(16, "0")
        else: # CWTable.CMD
            if cmd0reg in [CMDTable.ENA, CMDTable.OFF]:
                data_fame = "0"*16
            elif cmd0reg in [CMDTable.STP]:
                data_frame = str(hex(data))[2:].ljust(16, "0")
            elif cmd0reg in [CMDTable.MOV, CMDTable.POS, CMDTable.RMV]:
                data_frame = str(float2hex(data))[2:].ljust(16, "0")
            elif cmd0reg in [CMDTable.READ_DATA_REGS, CMDTable.READ_STATUS_REGS]:
                data_frame = str(hex(data[0]))[2:].ljust(2, "0") + str(hex(data[1]))[2:].ljust(2, "0") +"0"*12


            cmd0reg = cmd0reg.value

        ext_frame = "000" + tar.value + ("0" if tar != DeviceTable.BroadCast else "1") + src.value + cw.value + cmd0reg
        print("Bin Ext:", ext_frame)
        ext_frame = str(hex(int(ext_frame, 2)))[2:].rjust(8, "0")
        print("%s#%s"%(ext_frame, data_frame))

        pass


# CommonCMD.easy_cmd(tar=DeviceTable.BroadCast, src=DeviceTable.SliderX0, cw=CWTable.CMD, cmd0reg=CMDTable.READ_STATUS_REGS, data=[0,1])
# print(hex2int32("00012132"))
