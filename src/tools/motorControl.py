import os
import can
import time
import sys
# can0 = can.interface.Bus(channel = 'can0', bustype = 'socketcan_ctypes')# socketcan_native
motor = 0x02
# def receive():
#     # msg = can0.recv()
#     print(msg)
#     return msg
def enableMotor(targetid):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x01
    dataTx=[targetid,0,0,0,0,0,0,0]
    # print('dataTx',dataTx)
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    # can0.send(msg)
    time.sleep(0.1)

def disableMotor(targetid):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x02
    dataTx=[targetid,0,0,0,0,0,0,0]
    # print('dataTx',dataTx)
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    # can0.send(msg)
    time.sleep(0.1)
def move(targetid,speed):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x05
    dataTx=[targetid,0,0,0,speed[0],speed[1],speed[2],speed[3]]
    # print('dataTx',dataTx)
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    # can0.send(msg)
    time.sleep(0.1)
def stop(targetid):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x04
    dataTx=[targetid,0,0,0,0,0,0,0]
    # print('dataTx',dataTx)
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    # can0.send(msg)
    time.sleep(0.1)
def org(targetid):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x03
    dataTx=[targetid,0,0,0,0,0,0,0]
    # print('dataTx',dataTx)
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    # can0.send(msg)
    time.sleep(0.1)
def zerostart(targetid):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x09
    dataTx=[targetid,0,0,0,0,0,0,0]
    # print('dataTx',dataTx)
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    # can0.send(msg)
    time.sleep(0.1)
def sv(targetid):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x07
    dataTx=[targetid,0,0,0,0,0,0,0]
    # print('dataTx',dataTx)
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    # can0.send(msg)
    time.sleep(0.1)
def moveto(targetid,pos):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x06
    dataTx=[targetid,0,0,0,pos[0],pos[1],pos[2],pos[3]]
    # print('dataTx',dataTx)
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    # can0.send(msg)
    time.sleep(0.1)
def rmv(targetid,pos):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x0B
    dataTx=[targetid,0,0,0,pos[0],pos[1],pos[2],pos[3]]
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    # can0.send(msg)
def readStReg(targetid,addr,cnt):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x1E
    dataTx=[targetid,0,0,0,addr,cnt,0,0]
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    # print(msg)
    # can0.send(msg)
def readDtReg(targetid,addr,cnt):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x1F
    dataTx=[targetid,0,0,0,addr,cnt,0,0]
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    # can0.send(msg)
def writeDtReg(targetid,addr,value):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x20
    dataTx=[targetid,addr,0,0,value[0],value[1],value[2],value[3]]
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    # can0.send(msg)
def ppsset(targetid,pps):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x0c
    dataTx=[targetid,0,0,0,pps[0],pps[1],pps[2],pps[3]]
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    # can0.send(msg)

def ppsrun(targetid,pps):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x21
    dataTx=[targetid,0,0,0,pps[0],pps[1],pps[2],pps[3]]
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    # can0.send(msg)
def ppsgp(targetid,pps):
    id = 0
    id |= motor<<16
    #第几帧
    id |= 1<<12
    #共几帧
    id |= 1<<8
    #指令代码
    id |= 0x22
    dataTx=[targetid,0,0,0,pps[0],pps[1],pps[2],pps[3]]
    msg = can.Message(arbitration_id=id, data=dataTx, extended_id=True)
    print(msg)
    # can0.send(msg)

# if __name__ == "__main__":
#     if sys.argv[1] == 'enable':
#         # enableMotor(0x5)
#         time.sleep(1)
#         enableMotor(0x1)
#     elif sys.argv[1] == 'disable':
#         disableMotor(0x05)
#     elif sys.argv[1] == 'move':
#         #neg 0xFFFFFFCE00
#         move(0x01,[0x45,0xc8,0x00,0x00])
#     elif sys.argv[1] == 'stop':
#         stop(0x01)
#     elif sys.argv[1] == 'moveto':
#         moveto(0x01,[0x00,0x00,0x00,0x00])
#     elif sys.argv[1] == 'org':
#         org(0x01)
#     elif sys.argv[1] == 'rmv':
#         #neg ffe6ff
#         # rmv(0x01,[0xFF,0xFF,0xE6,0xFF])
#         rmv(0x01,[0x00,0x00,0x19,0x00])
#     elif sys.argv[1] == 'zerostart':
#         zerostart(0x01)
#     elif sys.argv[1] == 'sv':
#         sv(0x01)
#     elif sys.argv[1] == 'readStReg':
#         readStReg(0x01,0x01,0x01)
#     elif sys.argv[1] == 'readDtReg':
#         readDtReg(0x00,0x00,0x01)
#     elif sys.argv[1] == 'writeDtReg':
#         writeDtReg(0x01,0x08,[0x00,0x00,0x00,0x00])
#     elif sys.argv[1] == 'ppsset':
#         ppsset(0x01,[0x00,0x00,0x19,0x00])
#     elif sys.argv[1] == 'ppsrun':
#         ppsrun(0x01,[0x00,0x00,0x00,0x00])
#     elif sys.argv[1] == 'ppsgp':
#         #滑台组
#         ppsgp(0x01,[0x00,0x00,0x00,0x00])
        
ppsgp(0x01,[0x00,0x01,0x38,0x80])
        

