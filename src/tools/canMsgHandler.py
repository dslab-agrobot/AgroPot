import time
import can
from enum import IntEnum,Enum

def initBuses(cfgs):
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

    def __init__(self, message):
        ext_msg = str(bin(message.arbitration_id))[2:].rjust(29, "0")

        data_msg = []
        for asc in message.data:
            data_msg.append(hex(asc))


        print(ext_msg, data_msg)

        #: Array to storage binary data converted by msg.data
        # value = []
        # Data frame Part
        # bytes_value=bytes(msg.arbitration_id).decode(encoding="utf-8")
        # for asc in bytes_value:
        #    value.append(str(bin(ord(asc)))[:].rjust(4,"0"))

        # self._extID = value
        # print(value,value[0:5])

    class CanExtFrame(object):

        class _ExtIdTable(IntEnum):
            BIT27 = 0
            _target_id_0 = 1
            _target_id_1 = 10
            BIT18 = 10
            _source_id_0 = 11
            _source_id_1 = 20
            C0 = 20
            C1 = 21
            CMD0REG_0 = 22

        class DeviceTable(Enum):
            BroadCast = "000000000"
            SliderX0 = "000000001"
            SliderX1 = "000000010"
            SliderY = "000000011"
            SliderZ = "000000101"
            Pi = "000000110"

        class _CWTable(Enum):
            R_Stat_Reg = "00"  # "Read Status Register"
            R_Data_Reg = "01"  # "Read Data Register"
            W_Data_Reg = "10",  # "Write Data Register"
            CMD = "11",  # "Command"

        def __init__(self, ext_msg):
            """Decode the can message specific  in VSMD1X6_SERIES CAN MOTER

                    :type msg: can.message.Message

                    .. note:
                        Message.data could bring 8 bytes data maxium, which equals 2*8=16 hex digit
                        Message.dlc means the count of data, which may be used for error checking (I AM NOT SHURE)

                    """

            #: Extend identifier with 29 bits
            self._extID = ""

            #: Target ID self._extid[]
            self._target_id = ""

            self.target_device = self.DeviceTable.Pi

            self._source_id = ""

            self.source_device = self.DeviceTable.SliderX0

            self._cw = ""

            self._cmd0regAdr = ""

            #: msg.arbitration_id is int , we need a string type of bin-array
            self._extID = str(bin(ext_msg))[2:].rjust(29, "0")

            self._target_id = self._extID[self._ExtIdTable._target_id_0:self._ExtIdTable._target_id_1]

            self.target_device = self.DeviceTable(self._target_id)

            self._source_id = self._extID[self._ExtIdTable._source_id_0:self._ExtIdTable._source_id_1]

            self.source_device = self.DeviceTable(self._source_id)

            self._cw = self._CWTable((self._extID[self._ExtIdTable.C0:self._ExtIdTable.C1 + 1]))

            print("From: %s \nTo: %s\nCMD0RegAgr: %s \n" % (self.source_device, self.target_device, self._cw))

    class CanDataFrame(object):
        pass





    

if __name__=="__main__":
    bus = can.interface.Bus(bustype='socketcan', channel='vcan0', bitrate=500000)
    while True:
        for msg in bus:
            #print(dir(msg))
            #print(msg.arbitration_id)
            #print(msg.channel)
            can = CanFrame(msg)
            #print(type(msg.data))
