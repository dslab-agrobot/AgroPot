import time
import can
from enum import Enum

bus = can.interface.Bus(bustype='socketcan', channel='vcan0', bitrate=500000)

class canFrame(object):
    
    class _extID_table(Enum):
        BIT27 = 3
        TARGET_ID_0 = 4
        TARGET_ID_1 = 13
        BIT18 = 13
        SOURCE_ID_0 = 14
        SOURCE_ID_1 = 23
        C1 = 23
        c2 = 24 
        CMD0REG_0 = 25

    def __init__(self):
         
        #: Extend identifier with 29 bits 
        self._extID = [bin(0)]
        
        #: Data frame with 8 byte (32 bits)
        self._data = [bin(0)]
        
        #: Target ID self._extid[]
        self.target_id = int(0)
        
        self.source_id = int(0)

        self.cw = bin(0)

        self.cmd0regAddr = bin(0)
        
        pass

    def decodeMsg(self,msg):
        """Decode the can message specific  in VSMD1X6_SERIES CAN MOTER
        
        :type buses: can.message.Message
        :param buses: message for one frame 
    
        .. note:
            Message.data could bring 8 bytes data maxium, which equals 2*8=16 hex digit
            Message.dlc means the count of data, which may be used for error checking (I AM NOT SHURE)
    
        """
        #: Array to storage binary data converted by msg.data
        value = []
        
        #: msg.data is (byterarray)
        #: bytearray -> bytes -> string ;  
        bytes_value=bytes(msg.data).decode(encoding="utf-8")
    
        for asc in bytes_value:
            value.append(bin(ord(asc)))
        value = str(value)
    
        self._extID = value[self] 
        print(value)

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





    

if __name__=="__main__":
    while True:
        for msg in bus:
            decodeMsg(msg)
            #print(dir(msg))
            #print(msg.dlc)
            #print(msg.data)
            #print(type(msg.data))
