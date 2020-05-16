import can
import time
from VSMD1X6 import *
from multiprocessing import Process


class CanFrame(object):
    """ Per Frame in CAN-Network

    Use message in socket-can-bus to initialize,
    """
    class CANWarning(Enum):
        DlcCountWarring = 1

    class CANError(Enum):
        ExtTarIdNotFound = 101
        ExtSrcIdNotFound = 102
        DataStatusError = 103

    class _DataConverter(object):
        @staticmethod
        def hex2float(value):
            i = int(value, 16)  # convert from hex to a Python int
            cp = pointer(c_int(i))  # make this into a c integer
            fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
            return fp.contents.value

        @staticmethod
        def float2hex(value: float):
            cp = pointer(c_float(value))
            fp = cast(cp, POINTER(c_int))
            if value >= 0:
                return hex(fp.contents.value)
            else:
                return hex(int(fp.contents.value) & 0xFFFFFFFF)

        @staticmethod
        def int2hexstr(value, length):
            if type(value) == str:
                value = int(value)

            if value >= 0:
                value = hex(value)
            else:
                # Covert a signed hex number to a un-singed hex number
                value = hex(value & 0xFFFFFFFF)
            return value.rjust(length, "0")

        @staticmethod
        def hexstr2int(value):
            return int(value, 16)

        @staticmethod
        def hexstr2bin(value, length):
            return str(bin(int(value, 16)))[2:].rjust(length, "0")

        @staticmethod
        def byte2hexstr(value):
            return str(hex(value))[2:].rjust(2, "0")

        @staticmethod
        def int2binstr(value, length):
            if type(value) == str:
                value = int(value)
            return str(bin(value))[2:].rjust(length, "0")

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

        # Data Length Code , Every two hex equals 1 DLC
        self.dlc = message.dlc

        # Errors in this CAN Frame
        # Note, the convert procedure will not be terminated when
        # error occurs. It will just record all of them for debugging
        self.errors = []

        self.warnings = []

        # message.arbitration_id will be str or int , so we need to
        # convert it to int that we can use bin() to covert
        if type(message.arbitration_id) == str:
            message.arbitration_id = self._DataConverter.hexstr2int(message.arbitration_id)

        # :type message.arbitration_id : int
        # Convert this int to bin and use string to storage
        ext_msg = self._DataConverter.int2binstr(message.arbitration_id, 29)

        # :type [str,]
        # Have 0 , 1 or 2 set , 4 DLC mix a sub data_msg
        data_msg = []


        # :type message.data : bytearray
        # Each element convert to an int in bytearray iteration
        # Note That DLC can be 0,1,2...8,
        i = 0
        for t_int in message.data:
            # Every two dlc data get 32-bit , which can be used for a register
            if i % 4 == 0:
                data_msg.append(self._DataConverter.byte2hexstr(t_int))
            else:
                f_i = int(i/4)
                data_msg[f_i] += self._DataConverter.byte2hexstr(t_int)

            i += 1

        # Formatted Raw Data message , set for debug
        raw_dm = ""
        for i in range(data_msg.__len__()):
            # Make sure that each sub data_msg len 8 hex
            data_msg[i] = data_msg[i].ljust(8, "0").upper()
            raw_dm += data_msg[i]

        self.debug_msg = self.log_end()
        self.debug_msg += self.log_formatter(
            "Raw CAN Frame: ",
            [("Raw", self._DataConverter.int2hexstr(message.arbitration_id, 8) + "#"+raw_dm),
             ("Sender", self.channel),
             ("Extent ID Frame", ext_msg),
             ("DLC", self.dlc),
             ("Data Frame", data_msg)]
        )

        if self.dlc % 2 != 0:
            self.errors.append([self.CANWarning.DlcCountWarring, "DLC of this frame is %d" % self.dlc])
        if debug:
            print(self.debug_msg)

        self.ext_frame = self.CanExtFrame(ext_msg, debug=debug)

        # if self.ext_frame.DEVICE_ERR_FLG:
        #     return

        self.data_frame = self.CanDataFrame(data_msg=data_msg, dlc=self.dlc, cw=self.ext_frame.cw,
                                            cmd0adr=self.ext_frame.cmd0regAdr, debug=debug)
        if not self.errors and not self.ext_frame.errors and not self.data_frame.errors:
            self.ERROR_FLG = False
        else:
            self.ERROR_FLG = True
            error_list = []
            for el in self.errors + self.ext_frame.errors + self.data_frame.errors:
                error_list.append(("%s : %d " % (el[0].name, el[0].value), el[1]))
            _debug_msg = CanFrame.log_formatter(
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                error_list)
            with open("/home/pi/log.txt", "a+") as file:
                file.write(_debug_msg)

        # if self.ERROR_FLG or self.ext_frame.ERROR_FLG or self.data_frame.ERROR_FLG:
        #     debug_msg = self.debug_msg + self.ext_frame.debug_msg + self.data_frame.debug_msg
        #     with open("/home/pi/log.txt", "a+") as file:
        #         debug_msg = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n" + debug_msg + "\n"
        #         file.write(debug_msg)

    class CanExtFrame(object):
        """CAN Extend Identifier Frame

        You can find the detail of the frame-design for VSMD in ExtIdTable

        """

        def __init__(self, ext_msg, debug=False):
            """Decode the ext can message

                    :type ext_msg: str

                    .. note:
                        Message.data could bring 8 bytes data maxium, which equals 2*8=16 hex Data
                        Message.dlc means the count of data, which may be used for error checking (I AM NOT SHURE)

            """

            #: msg.arbitration_id is int , we need a string type of bin-array
            self._extID = ext_msg

            # Errors in this CAN EXT Frame
            # Note, the convert procedure will not be terminated when
            # error occurs. It will just record all of them for debugging
            self.errors = []

            self.warnings = []

            self._target_id = self._extID[ExtIdTable.target_id_0:ExtIdTable.target_id_1]

            self._source_id = self._extID[ExtIdTable.source_id_0:ExtIdTable.source_id_1]

            try:
                self.target_device = DeviceTable(self._target_id)
            except ValueError as e:
                self.errors.append([CanFrame.CANError.ExtTarIdNotFound,
                                    "Target ID (%s) in EXT frame not found \n %s" %
                                    (self._target_id, e)])

            try:
                self.source_device = DeviceTable(self._source_id)
            except ValueError as e:
                self.errors.append([CanFrame.CANError.ExtSrcIdNotFound,
                                    "Source ID (%s) in EXT frame not found \n %s" %
                                    (self._source_id, e)])

            self.cw = self._extID[ExtIdTable.C0:ExtIdTable.C1 + 1]

            self.cmd0regAdr = self._extID[ExtIdTable.CMD0REG_0:]

            self.debug_msg = CanFrame.log_formatter(
                "Extend ID Frame",
                [("Source Device", self.source_device.name), ("Target Device", self.target_device.name),
                 ("Command Word", self.cw),
                 ("CMD or Register ADR", self.cmd0regAdr if CWTable(self.cw) != CWTable.CMD else CMDTable(self.cmd0regAdr).name)
            ])

            if debug:
                print(self.debug_msg)

    class CanDataFrame(object):

        def __init__(self, dlc, data_msg, cw, cmd0adr, debug=False):

            self.cw = CWTable(cw)

            # If Read Regs will get dlc = 2
            self.cnt_data = int(dlc/4) if dlc != 2 else 1

            self.regs_values = {}
            self.status = None

            # Errors in this CAN Frame
            # Note, the convert procedure will not be terminated when
            # error occurs. It will just record all of them for debugging
            self.errors = []

            self.warnings = []

            self.debug_msg = ""

            # 1.StatusRegister 2.StatusInStatReg 3.DataRegister
            def _fill_reg_inf(_cnt: int, _data, _my_t):
                _result = []

                try:
                    # Query which register to start
                    _reg = _my_t.query(cmd0adr)
                except ValueError as e:
                    # if _my_t is StatusRegTable and int(cmd0adr, 2) <= 16:
                    #     self.debug_msg += log_formatter("*** Warning ***",
                    #                                     [("Key Not Found", "No Key in table , reserved ?")])
                    return _result
                    # else:
                    #     return ""

                for _i in range(_cnt):
                    try:
                        if _i != 0:
                            _reg = _reg.next()
                        raw_data = _data[_i]

                        # Use float as Data format in these register
                        if _reg in [DataRegTable.SPD, DataRegTable.ACC, DataRegTable.DEC, DataRegTable.CRA,
                                    DataRegTable.CRN, DataRegTable.CRH, ]:
                            _result.append([_reg.name, CanFrame._DataConverter.hex2float(raw_data)])
                        # Use int as Data format in these register
                        elif _reg in [DataRegTable.CID, DataRegTable.MCS]:
                            _result.append([_reg.name, CanFrame._DataConverter.hexstr2int(raw_data)])
                        # Use Enum for Baud rate
                        elif _reg == DataRegTable.BDR:
                            try:
                                _result.append([_reg.name, BaudRateDict[raw_data]])
                            except KeyError as e:
                                print("BaudRate Set Error", e)
                                print(BaudRateDict)
                                raise e
                        else:
                            _result.append([_reg.name, CanFrame._DataConverter.hexstr2int(raw_data)])
                    except ValueError as e:
                        war_log = CanFrame.log_formatter("Warning", [("Message", e)])
                        print(war_log)
                        break
                return _result

            # Check every bit in Status in Status Register
            def _fill_stat_value_inf(_data):

                # 32bit and fill zero in left
                _data = str(bin(int(_data, 16)))[2:].rjust(32, "0")

                # Reverse this string because it count from right
                _data = _data[::-1]
                _result = []
                for record in StatusValueTable:
                    _v = _data[record.value[0]]
                    if record in SafeInf and _v == "1":
                        self.errors.append([CanFrame.CANError.DataStatusError,
                                            record.value[1], _v + " / " + record.value[2]])
                return _result

            if self.cw == CWTable.R_Stat_Reg:
                self.regs_values = _fill_reg_inf(_cnt=self.cnt_data, _data=data_msg, _my_t=StatusRegTable)
                # Whatever you got , STATUS is the last one you got
                keys = [x[0] for x in self.regs_values]

                if "STATUS" in keys:        # and "SPD" not in keys: #todo test for debugging
                    # RegTable is [POS,STATUS]
                    if "POS" in keys:
                        self.status = _fill_stat_value_inf(data_msg[1])
                    # RegTable is [STATUS]
                    else:
                        self.status = _fill_stat_value_inf(data_msg[0])
            elif self.cw == CWTable.R_Data_Reg:
                self.regs_values = _fill_reg_inf(_cnt=self.cnt_data, _data=data_msg, _my_t=DataRegTable)
            elif self.cw == CWTable.W_Data_Reg:  # Write one register Once
                self.regs_values = _fill_reg_inf(1, _data=data_msg, _my_t=DataRegTable)
            elif self.cw == CWTable.CMD:
                self.command = CMDTable(cmd0adr)

            self.debug_msg += CanFrame.log_formatter("Action", [("CW Means", self.cw.name)])
            if self.cw in [CWTable.W_Data_Reg, CWTable.R_Data_Reg]:
                self.debug_msg += CanFrame.log_formatter("Data Frame - Data Reg", self.regs_values)
            elif self.cw == CWTable.CMD:
                data_frame = []
                if self.command in [CMDTable.ENA, CMDTable.OFF]:
                    pass
                elif self.command in [CMDTable.STP]:
                    data_frame.append((self.command.name, int(data_msg[0], 16)))
                elif self.command in [CMDTable.MOV, CMDTable.POS, CMDTable.RMV]:
                    data_frame.append((self.command.name, hex2float(data_msg[0])))
                elif self.command == CMDTable.READ_DATA_REGS:
                    d1 = data_msg[0][:2]
                    d2 = data_msg[0][2:4]
                    data_frame.append(("Data Reg Start:", DataRegTable.query(CanFrame._DataConverter.hexstr2bin(d1, 7))))
                    data_frame.append(("Data Reg count:", int(d2, 16)))
                elif self.command == CMDTable.READ_STATUS_REGS:
                    d1 = data_msg[0][:2]
                    d2 = data_msg[0][2:4]
                    data_frame.append(("Data Reg Start:", StatusRegTable.query(CanFrame._DataConverter.hexstr2bin(d1, 7))))
                    data_frame.append(("Data Reg count:", int(d2, 16)))
                else:
                    data_frame.append((self.command.name, int(data_msg, 16)))
                self.debug_msg += CanFrame.log_formatter("Data Frame", [("Command", data_frame)])
            else: #CWTable.R_Stat_Reg
                keys = [x[0] for x in self.regs_values]
                if "POS" in keys or "SPD" in keys:
                    self.debug_msg += CanFrame.log_formatter("Data Frame - Stat Reg", self.regs_values)
            self.debug_msg += CanFrame.log_end()
            if debug:
                print(self.debug_msg)

    @staticmethod
    def log_formatter(title, tcs):
        result = "| %s | \n" % title
        for tc in tcs:
            result += "+ %-22s :  %s \n" % (tc[0], tc[1])
        return result

    @staticmethod
    def log_end():
        return "%s\n" % ("*" * 60)


class CanMsgListener(Process):

    def __init__(self, channel="can0", bitrate=500000):
        super(CanMsgListener, self).__init__()
        self.channel = channel
        self.bitrate = bitrate
        self.debug_msg = ""
        self.cnt = 0

    def run(self):
        _bus = can.interface.Bus(bustype='socketcan', channel=self.channel, bitrate=self.bitrate)
        while True:
            for _msg in _bus:
                self.cnt += 1
                canframe = CanFrame(_msg, debug=False)
                if canframe.ERROR_FLG == True:
                    self.debug_msg = canframe.debug_msg
                    print(canframe.debug_msg)
                    self.terminate()


class CANFunctionList(object):

    @staticmethod
    def move(direction: str, distance: int, bus: can.interface.Bus):
        direction = direction.upper()
        if direction == "X":
            time_estimate = abs(1.0 * distance/spd)
            for cmd in [CommonCMD.enable_motor("ALL"), CommonCMD.disable_motor("Y"),
                   CommonCMD.disable_motor("Z"), CommonCMD.move_dis("ALL", distance)]:
                print(cmd)
                bus.send(str2canmsg(cmd))
            time.sleep(time_estimate + 1)
            bus.send(str2canmsg(CommonCMD.disable_motor("ALL")))





def str2canmsg(raw_cmd: str):
    extid = int(raw_cmd.split("#")[0], 16)
    data_frame = []
    datas = raw_cmd.split("#")[1]
    for i in range(int(datas.__len__()/2)):
        data_frame.append(int(datas[i*2:i*2 + 2], 16))
    msg_snd = can.Message(arbitration_id=extid, channel="can0",
                          data=data_frame,
                          is_extended_id=True)
    return msg_snd

if __name__ == "__main__":
    pass
    bus = can.interface.Bus(bustype='socketcan', channel='vcan0', bitrate=500000)
    cnt = 0
    while True:
        for msg in bus:
            print("\n%2d\n" % cnt)
            cnt += 1
            can = CanFrame(msg, debug=True)
    # msg = str2canmsg("0004079F#002F")
    # print(type(msg.arbitration_id))
    # can = CanFrame(msg, debug=True)
