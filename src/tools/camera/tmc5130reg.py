import json
import math
import tmc_spi
import sys
filename = 'tmc5130reg_list.json'

#本地寄存器表：预更新对应寄存器对应属性
#修改json文件中具体Attribute的current值
#也可以GUI或直接修改json文件
def modAttribute_local(regname:str,attribute_name:str,value:str):
    with open(filename) as f:
        reg_list = json.load(f)
        f.close()
    checkRules(regname,attribute_name,value)
    reg_list[regname]['attribute'][attribute_name]['current'] = value
    with open(filename,'w') as f:
        json.dump(reg_list, f, ensure_ascii=False, indent=4)
        f.close()

#本地寄存器表：将寄存器内所有预更新的属性生成到Reg current
def updateReg_local(regname:str):
    with open(filename) as f:
        reg_list = json.load(f)
        f.close()

    tmp_reg_value = int(reg_list[regname]['default'],16)
    attributes = reg_list[regname]['attribute']
    for i in attributes:#i='mres'
        tmp_reg_value = changeBinBit(tmp_reg_value,int(attributes[i]['current'],16),int(attributes[i]['bit_start'],10),int(attributes[i]['bit_end'],10))
        # print('tmp:%#x'%tmp_reg_value)

    reg_list[regname]['current'] = '%x'%tmp_reg_value
    with open(filename,'w') as f:
        json.dump(reg_list, f, ensure_ascii=False, indent=4)
        f.close()

#参数为寄存器名，加载到TMC5130寄存器
#parm1:regname
#parm2:True--load default False--load current
def load2Reg(regname:str,config_default:bool):
    with open(filename) as f:
        reg_list = json.load(f)
        f.close()
    addr = int(reg_list[regname]['address'],16)
    if config_default:
        value = int(reg_list[regname]['default'],16)
    else :
        value = int(reg_list[regname]['current'],16)
    tmc_spi.writeReg(addr,value)

#参数为寄存器名，从TMC5130寄存器读取并打印到控制台
#parm1:Regname
def readFromReg(regname:str):
    with open(filename) as f:
        reg_list = json.load(f)
        f.close()
    addr = int(reg_list[regname]['address'],16)
    readResult = tmc_spi.readReg(addr)
    print('read {:s}:'.format(regname))
    print('\n'.join('{}:{:0=2x}'.format(*k) for k in enumerate(readResult)))
    return readResult

#位操作：改变对应位的值
#e.g. origin=0xffff tarValue:0x6 tarBitStart:4 tarBitend:7 changed_origin:0xff6f
def changeBinBit(origin:int,tarValue:int,tarBitStart:int,tarBitend:int):
    #temp生成用于清掉原来的值
    temp = 0
    for i in range (tarBitend-tarBitStart+1):
        temp += int(math.pow(2,i))
    tmp_origin = origin&(~(temp<<tarBitStart))
    changed_origin = tmp_origin|(tarValue<<tarBitStart)
    return changed_origin

#判断值的合法性
def checkRules(regname:str,attribute_name:str,value:str):  
    with open(filename) as f:
        reg_list = json.load(f)
        f.close()
    if(reg_list[regname]['attribute'][attribute_name]['type']=='select'):
        if(value not in reg_list[regname]['attribute'][attribute_name]['choice'].values()):
            print('regname:%s value ERROR'%regname)
            sys.exit(1)
    elif(reg_list[regname]['attribute'][attribute_name]['type']=='input'):
        bit_start = int(reg_list[regname]['attribute'][attribute_name]['bit_start'],10)
        bit_end = int(reg_list[regname]['attribute'][attribute_name]['bit_end'],10)
        #设定值都应看作二进制序列，没有数值意义。在TMC5130解析出来以后（部分reg以补码解析），才有数值意义
        #以数值来判断传入位数
        val = pow(2,bit_end-bit_start+1)
        if(not((int(value,16)>=0)&(int(value,16)<val))):
            print('regname:%s value ERROR'%regname)
            sys.exit(1)


