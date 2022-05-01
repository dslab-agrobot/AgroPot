import spidev
import time
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=4000000
spi.mode = 0b11
def writeReg(address,datagram):   
    address += 0x80 #write reg needed
    i_datagram = []
    i_datagram.append(address)

    for i in range(4):
        tmp = 24-8*i
        tmp = (datagram>>tmp)&(0xFF)
        i_datagram.append(tmp)
    readVals=spi.xfer(i_datagram)


def readReg(address): 
    datagram = 0x0
    i_datagram = []
    i_datagram.append(address)
    for i in range(4):
        tmp = 24-8*i
        tmp = (datagram>>tmp)&(0xFF)
        i_datagram.append(tmp)
    readVals = spi.xfer(i_datagram)
    i_datagram2 = [0xFF,0xFF,0xFF,0xFF,0xFF]
    readVals2 = spi.xfer(i_datagram2)
    time.sleep(0.1)
    return readVals2[1:5]

def readReg1(address): 
    datagram = 0x0
    i_datagram = []
    i_datagram.append(address)
    for i in range(4):
        tmp = 24-8*i
        tmp = (datagram>>tmp)&(0xFF)
        i_datagram.append(tmp)
    readVals = spi.xfer(i_datagram)
    i_datagram2 = [0xFF,0xFF,0xFF,0xFF,0xFF]
    readVals2 = spi.xfer(i_datagram2)
    time.sleep(0.1)
    return readVals2
  
