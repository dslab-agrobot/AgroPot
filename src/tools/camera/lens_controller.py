import tmc5130reg
import os
import sys
from enum import Enum,IntEnum
import argparse

BcmNum = 5

# spd µsteps/s
u_spd = 0.78678
# acc µsteps/s
u_acc = 79.2351


class DefaultValue(IntEnum):
    VMAX = 189  # F0 in reg
    AMAX = 1189  # F in reg
    VSTOP = 12  # F in reg


class MicroStep(Enum):
    full = "8"
    step2 = "7"
    step4 = "6"  
    step8 = "5"
    step16 = "4"
    step32 = "3"
    step64 = "2"
    step128 = "1"
    step256 = "0"


def _init_gpio():
    os.system("sudo echo %1d > /sys/class/gpio/export" % BcmNum)
    # print("echo %1d > /sys/class/gpio/export" % BcmNum)
    os.system("sudo echo out > /sys/class/gpio/gpio%1d/direction" % BcmNum)
    # print("init gpio")


def _release_gpio():
    os.system("sudo echo %1d > /sys/class/gpio/unexport" % BcmNum)


def _enable_motor():
    if tmc5130reg.readFromReg('GSTAT')[3] == 0x1:
        print('Power on reset success')

    tmc5130reg.load2Reg('GCONF', True)
    tmc5130reg.load2Reg('CHOPCONF', True)
    tmc5130reg.load2Reg('IHOLD_IRUN', True)
    tmc5130reg.load2Reg('PWMCONF', True)
    tmc5130reg.load2Reg('A1', True)
    tmc5130reg.load2Reg('V1', True)
    tmc5130reg.load2Reg('AMAX', True)
    tmc5130reg.load2Reg('VMAX', True)
    tmc5130reg.load2Reg('DMAX', True)
    tmc5130reg.load2Reg('D1', True)
    tmc5130reg.load2Reg('VSTART', True)
    tmc5130reg.load2Reg('VSTOP', True)
    tmc5130reg.load2Reg('TZEROWAIT', True)

    tmc5130reg.load2Reg('XACTUAL', True)
    tmc5130reg.load2Reg('XTARGET', True)


def _set_velocity(spd=DefaultValue.VMAX.value, acc=DefaultValue.AMAX.value):
    """

    :param speed: 0 - 51561, µsteps*hz , (2**16 - 1) * u_spd
    :param acc: 0 - 5192338, µsteps*hz , (2**16 - 1) * u_acc
    :return:
    """
    spd = int(spd / u_spd)
    acc = int(acc / u_acc)

    # The unit of V1 and VMAX is µsteps / t, that t = 2^24/fclk, fclk=13.2Mhz,
    # defined in tmc5130. 1 µsteps / t = 0.78678 µsteps/s
    tmc5130reg.modAttribute_local('V1', 'V1', hex(int(spd / 2)))
    tmc5130reg.modAttribute_local('VMAX', 'VMAX', hex(spd))
    tmc5130reg.updateReg_local('V1')
    tmc5130reg.updateReg_local('VMAX')
    tmc5130reg.load2Reg('V1', False)
    tmc5130reg.load2Reg('VMAX', False)

    # The unit of A1 and AMAX is µsteps / ta**2, that ta**2 = 2^41/fclk**2, fclk=13.2Mhz,
    # defined in tmc5130. 1 µsteps / t = 0.78678 µsteps/s
    tmc5130reg.modAttribute_local('A1', 'A1', hex(int(acc / 2)))
    tmc5130reg.modAttribute_local('AMAX', 'AMAX', hex(acc))
    tmc5130reg.updateReg_local('A1')
    tmc5130reg.updateReg_local('AMAX')
    tmc5130reg.load2Reg('A1', False)
    tmc5130reg.load2Reg('AMAX', False)


def _move_enabled(offset):
    tmc5130reg.modAttribute_local('CHOPCONF', 'mres', MicroStep.full.value)
    tmc5130reg.updateReg_local('CHOPCONF')
    tmc5130reg.load2Reg('CHOPCONF', False)
    # '''
    # mod velocity
    # 0x0--0xffff
    # '''
    # tmc5130reg.modAttribute_local('V1', 'V1', 'F0')
    # tmc5130reg.modAttribute_local('VMAX', 'VMAX', 'F0')
    # tmc5130reg.updateReg_local('V1')
    # tmc5130reg.updateReg_local('VMAX')
    # tmc5130reg.load2Reg('V1', False)
    # tmc5130reg.load2Reg('VMAX', False)
    '''
    mod XACTUAL,XTARGET
    XACTUALL<XTARGET move forward
    XACTUALL>XTARGET move backward

    default:fullstep steps:2342=0x926
    |------------------------------------------|
    start--------------2342steps-------------end

    if microstep8 steps:2342*8=18736=0x4930
    ***DO NOT OUT OF THIS RANGE***
    '''
    if offset > 0:
        x0 = "0"
        x1 = str(offset)
    else:
        x1 = "0"
        x0 = str(-offset)
    tmc5130reg.modAttribute_local('XACTUAL', 'XACTUAL', x0)
    tmc5130reg.modAttribute_local('XTARGET', 'XTARGET', x1)
    tmc5130reg.updateReg_local('XACTUAL')
    tmc5130reg.updateReg_local('XTARGET')
    tmc5130reg.load2Reg('XACTUAL', False)
    tmc5130reg.load2Reg('XTARGET', False)


def _tmc_init():
    if os.path.exists("/sys/class/gpio/gpio%1d" % BcmNum):
        _release_gpio()
    _init_gpio()
    _enable_motor()


def _mode_switch(value=0):
    """
    Choose which motor to control

    :param value: 0 for zoom, 1 for focus
    :return:
    """

    os.system("sudo echo %1d > /sys/class/gpio/gpio%1d/value" % (value, BcmNum))


class LensController(object):

    def __init__(self):
        _tmc_init()
        self.focus = 0
        self.zoom = 0
        _set_velocity()
        self.zero()
        pass

    @staticmethod
    def move(motor, pct, spd=0):
        if motor not in ["f", "z"]:
            print('Invalid device, ["f","z"] for [focus, zoom]')
            return
        if motor == "z":
            _mode_switch(0)
        else:
            _mode_switch(1)

        if spd == 0:
            _set_velocity()
        elif spd > 0:
            _set_velocity(spd)
        else:
            print("Invalid speed")
            return

        if not -1 <= pct <= 1:
            print("Move percentage error, ranged in 0 to 1")
            return

        # 2342 plus for full step
        mcs = 2 ** abs(int(MicroStep.full.value) - 8)
        plus = int(pct * mcs * 2342)
        _move_enabled(plus)

    def zero(self, device='a'):
        """

        :param device: f,z,a for focus, zoom, all
        :return:
        """

        if device not in ["a", "f", "z"]:
            print('Invalid device, ["f","z","a"] for [focus, zoom, all]')
            return
        self.focus = 0
        self.zoom = 0
        if device == "a":
            self.move("f", -1)
            self.move("z", -1)
        elif device == "f":
            self.move("f", -1)
        elif device == "z":
            self.move("z", -1)


if __name__ == '__main__':
    _tmc_init()
    parser = argparse.ArgumentParser(description='Camera control test')
    parser.add_argument('mot', type=str, choices=["z", "f"], help='ZOOM(z) or FOCUS(F)')
    parser.add_argument('--spd', type=int, help='0 - 65535, default 240')
    parser.add_argument('len', type=int, help='2342 with full step')
    args = parser.parse_args()
    if hasattr(args, "speed"):
        _set_velocity(int(args.speed))
    else:
        _set_velocity()
    if args.mot == "z":
        _mode_switch(0)
    else:
        _mode_switch(1)

    _move_enabled(args.len)
