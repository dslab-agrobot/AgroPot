import can
from VSMD1X6 import *


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
            busses.append(can.interface.Bus(bustype='socketcan', channel=cfg[0], bitrate=cfg[1]))
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
                data_msg.append(str(hex(t_int))[2:].rjust(2, "0"))
            else:
                f_i = int((i-1)/2)
                data_msg[f_i] += str(hex(t_int))[2:].rjust(2, "0")
                print(hex2float(data_msg[f_i]))
                data_msg[f_i] = str(int(data_msg[f_i], 16))
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

        You can find the detail of the frame-design for VSMD in ExtIdTable

        """

        def __init__(self, ext_msg, debug=False):
            """Decode the ext can message

                    :type ext_msg: str

                    .. note:
                        Message.data could bring 8 bytes data maxium, which equals 2*8=16 hex digit
                        Message.dlc means the count of data, which may be used for error checking (I AM NOT SHURE)

            """

            #: msg.arbitration_id is int , we need a string type of bin-array
            self._extID = ext_msg

            self._target_id = self._extID[ExtIdTable.target_id_0:ExtIdTable.target_id_1]

            self.target_device = DeviceTable(self._target_id)

            self._source_id = self._extID[ExtIdTable.source_id_0:ExtIdTable.source_id_1]

            self.source_device = DeviceTable(self._source_id)

            self.cw = self._extID[ExtIdTable.C0:ExtIdTable.C1 + 1]

            self.cmd0regAdr = self._extID[ExtIdTable.CMD0REG_0:]

            if debug:
                debug_msg = log_formatter("Extend ID Frame", [
                    ("Source Device", self.source_device.name), ("Target Device", self.target_device.name),
                    ("Command Word", self.cw), ("CMD or Register ADR", self.cmd0regAdr if CWTable(self.cw) !=
                    CWTable.CMD else CMDTable(self.cmd0regAdr).name)
                ])
                print(debug_msg)

    class CanDataFrame(object):

        def __init__(self, dlc, data_msg, cw, cmd0adr, debug=False):

            self.cw = CWTable(cw)
            self.cnt_data = int(dlc/2)
            self.regs_values = {}
            self.status = None

            def _fill_reg_inf(_cnt: int, _data, _my_t: AwesomeOrderedDict):
                _result = []
                _last_key = "None"
                for _i in range(self.cnt_data):
                    try:
                        if _last_key == "None":
                            _last_key = cmd0adr
                        else:
                            _last_key = _my_t.next_key(_last_key)
                        _result.append(([_my_t[_last_key][0]], _data[_i]))
                    except ValueError as e:
                        war_log = log_formatter("Warning", [("Message", e)])
                        print(war_log)
                        break
                return _result

            def _fill_stat_value_inf(_data):
                _result = []
                for record in StatusValueTuple:
                    _v = _data[record[0]]
                    if _v == "1":
                        _result.append(
                            [record[2], _v, record[-1]]
                        )
                return _result

            if self.cw == CWTable.R_Stat_Reg:
                self.regs_values = _fill_reg_inf(_cnt=self.cnt_data, _data=data_msg, _my_t=StatusRegDict)
                # Whatever you got , STATUS is the last one you got
                if "STATUS" in self.regs_values.keys():
                    self.status = _fill_stat_value_inf(data_msg[self.regs_values.__len__()-1])

            elif self.cw == CWTable.R_Data_Reg or self.cw == CWTable.W_Data_Reg:
                self.regs_values = _fill_reg_inf(_cnt=self.cnt_data, _data=data_msg, _my_t=DigitRegDict)
            elif self.cw == CWTable.CMD:
                self.command = CMDTable(cmd0adr)

            if debug:
                debug_msg = log_formatter("Action", [("CW Means", self.cw.name)])
                if self.cw != CWTable.CMD:
                    debug_msg += log_formatter("Data Frame", self.regs_values)
                else:
                    debug_msg += log_formatter("Data Frame", [("Command",self.command.value)])
                if self.status is not None :
                    debug_msg += log_formatter("STATUS", self.status)
                debug_msg += log_end()
                # print(debug_msg)
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
    cnt = 0
    while True:
        for msg in bus:
            print("\n%2d\n" % cnt)
            cnt += 1
            can = CanFrame(msg, debug=True)
