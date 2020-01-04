import time
import can
from enum import IntEnum,Enum


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

    Use message in socket-can-bus to initialize
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
        # :type message.arbitration_id : int
        # Convert this int to bin and use string to storage
        ext_msg = str(bin(message.arbitration_id))[2:].rjust(29, "0")

        data_msg = []

        # :type message.data : bytearray
        # Each element convert to an int in bytearray iteration
        for t_int in message.data:
            data_msg.append(hex(t_int))

        if debug:
            print(ext_msg, data_msg)

        self.ext_frame = self.CanExtFrame(ext_msg)
        
        self.data_frame = self.CanDataFrame(data_msg)

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

        class CWTable(Enum):
            R_Stat_Reg = "00"  # "Read Status Register"
            R_Data_Reg = "01"  # "Read Data Register"
            W_Data_Reg = "10",  # "Write Data Register"
            CMD = "11",  # "Command"

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

        def __init__(self, ext_msg):
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

            self._cw = self.CWTable((self._extID[self._ExtIdTable.C0:self._ExtIdTable.C1 + 1]))

            self.cmd0regAdr = self._extID[self._ExtIdTable.CMD0REG_0:]

            print("From: %s \nTo: %s\nCMD: %s \nCMD0RegAgr: %s \n"
                  % (self.source_device, self.target_device, self._cw, self.cmd0regAdr))

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
