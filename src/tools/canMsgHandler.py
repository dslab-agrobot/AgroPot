import time
import can
from enum import IntEnum, Enum
from collections import OrderedDict


class MyOrderedDict(OrderedDict):
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
        print(self.name_key)


    def next_key(self, key):
        """Get next key in order

        :param key:
        :return:
        :raise ValueError :
            when we get a last key or the key is not in the dict
        """
        __index = self.__list.index(key)
        if __index >= self.__list.__len__():
            raise ValueError("{!r} is the last key".format(key))
        __next = self.__list[__index + 1]
        return __next

    def get_key(self,t_name):
        pass

    def first_key(self):
        for key in self:
            return key
        raise ValueError("OrderedDict() is empty")


def init_buses(cfgs):
    """Initialize CAN-buses in software
    
    Initialize the cab-buses first then you can use buses 
    to send or recieve messages
    
    :type cfgs: Array with cuple like (channel,bitrate)
    :param cfgs: List of CAN-BUS configure
    
    :return: buses

    :raise can.CanError
        if the initialization failed

    .. note::

        This method will just finish the set-up in software that assume you
        have complete your hardware installation

    """
    busses = []

    for cfg in cfgs:
        try:
            busses.append( can.interface.Bus(bustype='socketcan', channel=cfg[0], bitrate=cfg[1]))
        except can.CanError as e:
            print("CAN bus init failed in %s , "%cfg , e)

    return busses


class CanFrame(object):
    """ Per Frame in CAN-Network

    Use message in socket-can-bus to initialize,
    """

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

        # Data Length Code , Every two 0x para get 1 DLC
        self.dlc = message.dlc

        # :type message.arbitration_id : int
        # Convert this int to bin and use string to storage
        ext_msg = str(bin(message.arbitration_id))[2:].rjust(29, "0")

        # :type [str,]
        data_msg = []

        # :type message.data : bytearray
        # Each element convert to an int in bytearray iteration
        i = 0
        for t_int in message.data:
            # Every two dlc data get 32-bit , which can be used for a register
            if i % 2 == 0:
                data_msg.append(str(t_int).rjust(2, "0"))
            else:
                data_msg[int((i-1)/2)] += str(t_int).rjust(2, "0")
            i += 1

        if debug:
            debug_msg = log_end()
            debug_msg += log_formatter("Main: ", [
                ("Sender", self.channel), ("Extent ID Frame", ext_msg), ("DLC", self.dlc), ("Data Frame", data_msg)
            ])
            if self.dlc % 2 != 0:
                debug_msg += log_formatter("*** Warning ***", [("DLC Count warning", "DLC count should not be ODD")])
            print(debug_msg)

        self.ext_frame = self.CanExtFrame(ext_msg, debug=debug)
        
        self.data_frame = self.CanDataFrame(data_msg=data_msg, dlc=self.dlc, cw=self.ext_frame.cw,
                                            cmd0adr=self.ext_frame.cmd0regAdr, debug=debug)

    class CanExtFrame(object):
        """CAN Extend Identifier Frame

        You can find the detail of the frame-design for VSMD in _ExtIdTable

        """

        class _ExtIdTable(IntEnum):
            """Name of bits and their description

            xxx_id_0 and xxx_id_1 are used for slice of array
            like ">>> array[start:end] "

            """
            # Fixed value 0
            BIT27 = 0

            # Start of device ID for target
            # All zero (total 9) for broadcast
            _target_id_0 = 1

            # End of device ID for target
            _target_id_1 = 10

            # Fixed value 0
            BIT18 = 10

            # Start of device ID for source
            _source_id_0 = 11

            # End of device ID for source
            _source_id_1 = 20

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

        def __init__(self, ext_msg, debug=False):
            """Decode the ext can message

                    :type ext_msg: str

                    .. note:
                        Message.data could bring 8 bytes data maxium, which equals 2*8=16 hex digit
                        Message.dlc means the count of data, which may be used for error checking (I AM NOT SHURE)

            """


            #: msg.arbitration_id is int , we need a string type of bin-array
            self._extID = ext_msg

            self._target_id = self._extID[self._ExtIdTable._target_id_0:self._ExtIdTable._target_id_1]

            self.target_device = self.DeviceTable(self._target_id)

            self._source_id = self._extID[self._ExtIdTable._source_id_0:self._ExtIdTable._source_id_1]

            self.source_device = self.DeviceTable(self._source_id)

            self.cw = self._extID[self._ExtIdTable.C0:self._ExtIdTable.C1 + 1]

            self.cmd0regAdr = self._extID[self._ExtIdTable.CMD0REG_0:]

            if debug:
                debug_msg = log_formatter("Extend ID Frame", [
                    ("Source Device", self.source_device.name), ("Target Device", self.target_device.name),
                    ("Command Word", self.cw), ("CMD or Register ADR", self.cmd0regAdr)
                ])
                print(debug_msg)

    class CanDataFrame(object):

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

        DigitRegDict = MyOrderedDict({

            # ADR        Description   Value and Detail
            "0000000": ["Channel ID", "Determined by motor"],  # 0x00
            "0000001": ["Baud rate", "Default 132000"],  # 0x01
            "0000010": ["Motor Control Subdivision",
                        "0 : one step \n1 : 1/2\n2 : 1/4\n3 : 1/8\n4: 1/16\n5 : 1/32\n"
                        "6 : 1/64 (Ser-045,13X,14X Only)\n7:1/128 (Ser-045,13X,14X Only)\n"
                        "8 : 1/256 (Ser-045,13X,14X Only)"],  # 0x02
            "0000011": ["Target speed", "(-192000,192000)pps"],  # 0x03
            "0000100": ["Accelerate", "(0,192000000)pps/s"],  # 0x04
            "0000101": ["Decelerate", "(0,192000000)pps/s"],  # 0x05
            "0000110": ["Current Accelerate", "0-2.5A(Series-025)\n0-4.5A(Series-045)"],  # 0x06
            "0000111": ["Current Normal", "0-2.5A(Series-025)\n0-4.5A(Series-045)"],  # 0x07
            "0001000": ["Current Hold", "0-2.5A(Series-025)\n0-4.5A(Series-045)"],  # 0x08
            "0001001": ["Function Settings for S1,S2", "See SensorValueTable"],  # 0x09
            "0001010": ["Function Settings for S3,S4", "See SensorValueTable"],  # 0x0A
            "0001011": ["Function Settings for S5,S6", "See SensorValueTable"],  # 0x0B
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

        StatusRegDict = MyOrderedDict({
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

        def __init__(self, dlc, data_msg, cw, cmd0adr, debug=False):

            self.cw = self.CWTable(cw)
            self.cnt_data = int(dlc/2)
            self.regs_values = {}
            self.status = None

            def _fill_reg_inf(_cnt: int, _data, _my_t: MyOrderedDict):
                _result = []
                _last_key = "None"
                for _i in range(self.cnt_data):
                    if _last_key == "None":
                        _last_key = cmd0adr
                    else:
                        _last_key = _my_t.next_key(_last_key)
                    _result.append(([_my_t[_last_key][0]], _data[_i]))
                return _result

            def _fill_stat_value_inf(_data):
                _result = []
                for record in self.StatusValueTuple:
                    _v = _data[record[0]]
                    _result.append(
                        [record[2], _v, record[-1] if _v == "1" else "Default"]
                    )
                return _result

            if self.cw == self.CWTable.R_Stat_Reg:
                self.regs_values = _fill_reg_inf(_cnt=self.cnt_data, _data=data_msg, _my_t=self.StatusRegDict)
                # Whatever you got , STATUS is the last one you got
                if "STATUS" in self.regs_values.keys():
                    self.status = _fill_stat_value_inf(data_msg[self.regs_values.__len__()-1])

            elif self.cw == self.CWTable.R_Data_Reg or self.cw == self.CWTable.W_Data_Reg:
                self.regs_values = _fill_reg_inf(_cnt=self.cnt_data, _data=data_msg, _my_t=self.DigitRegDict)
            elif self.cw == self.CWTable.CMD:
                self.command = self.CMDTable(cmd0adr)

            if debug:
                debug_msg = log_formatter("Action", [("CW Means", self.cw.name)])
                if self.cw != self.CWTable.CMD:
                    debug_msg += log_formatter("Data Frame", self.regs_values)
                else:
                    debug_msg += log_formatter("Data Frame", [("Command",self.command.value)])
                if self.status is not None :
                    debug_msg += log_formatter("STATUS", self.status)
                debug_msg += log_end()
                print(debug_msg)
            pass

    @classmethod
    def easy_cmd(cls,):
        pass


def log_formatter(title, tcs):
    result = "\033[1;32m%s \033[0m\n" % title
    for tc in tcs:
        result += "%-22s : \033[1;34m %s \033[0m\n" % (tc[0], tc[1])
    return result


def log_end():
    return "\033[1;36m%s\033[0m\n" % ("*"*60)


if __name__ == "__main__":
    bus = can.interface.Bus(bustype='socketcan', channel='vcan0', bitrate=500000)
    while True:
        for msg in bus:
            can = CanFrame(msg, debug=True)
