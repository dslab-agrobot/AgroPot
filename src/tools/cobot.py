import time, random, subprocess
from enum import Enum
from pymycobot.mycobot import MyCobot
# from pythonAPI.mycobot3 import MyCobot as MyCobot3
from pymycobot.genre import Angle, Coord
import cv2
from detector import *
import numpy as np

# degree to radian
d2r = 0.17453


def sample():
    port = subprocess.check_output(['echo -n /dev/ttyUSB*'], shell=True).decode()
    mycobot = MyCobot(port)

    print('Start check api\n')

    print('::get_angles()')
    print('==> degrees: {}\n'.format(mycobot.get_angles()))
    time.sleep(0.5)

    # mycobot.state(AngleAnimation.Start)

    # print('::get_radians()')
    # print('==> radians: {}\n'.format(mycobot.get_radians()))
    # time.sleep(0.5)
    #

    # print('::send_angles()')
    # mycobot.send_angles([0,0,0,0,0,0], 80)
    # print('==> set angles [0,0,0,0,0,0], speed 30\n')
    # print('Is moving: {}'.format(mycobot.is_moving()))
    # time.sleep(5)
    #
    # print('::send_angles()')
    # mycobot.send_angle(Angle.J1.value, 20, 80)
    # # mycobot.send_angles([0, 40, 0, 0, 0, 0], 80)
    # # print('==> set angles [0,0,0,0,0,0], speed 30\n')
    # print('Is moving: {}'.format(mycobot.is_moving()))
    # time.sleep(4)
    #
    # print('::send_angles()')
    # mycobot.send_angles(Init_Angle, 80)
    # print('==> set angles [0,0,0,0,0,0], speed 80\n')
    # print('Is moving: {}'.format(mycobot.is_moving()))
    # time.sleep(3)

    #
    # print('::send_radians')
    # mycobot.send_radians([1,1,1,1,1,1], 70)
    # print('==> set raidans [1,1,1,1,1,1], speed 70\n')
    # time.sleep(1.5)
    #
    # print('::send_angle()')
    # mycobot.send_angle(Angle.J2.value, 10, 50)
    # print('==> angle: joint2, degree: 10, speed: 50\n')
    # time.sleep(1)
    #
    # print('::get_coords()')
    # print('==> coords {}\n'.format(mycobot.get_coords()))
    # time.sleep(0.5)
    #
    # print('::send_coords()')
    # coord_list = [160, 160, 160, 0, 0, 0]
    # mycobot.send_coords(coord_list, 70, 0)
    # print('==> send coords [160,160,160,0,0,0], speed 70, mode 0\n')
    # time.sleep(3.0)
    #
    # print(mycobot.is_in_position(coord_list, 1))
    # time.sleep(1)
    #
    # print('::send_coord()')
    # mycobot.send_coord(Coord.X.value, -40, 70)
    # print('==> send coord id: X, coord value: -40, speed: 70\n')
    # time.sleep(2)

    # print('::set_free_mode()')
    # mycobot.set_free_mode()
    # print('==> into free moving mode.')
    # print('=== check end <==\n')


class AngleAnimation(Enum):
    Start = [15.9, -24.91, -26.66, -26.79, -14.23, 24.91],
    Prepare = [0, -24, -26, -2.5, 0, 24.91],
    Observer = [0, 15, 0, -16.8, 0, 24.91],


def state(self, clip: AngleAnimation, speed=70):
    current = self.get_angles()
    offset_max = 0
    for i, j in zip(clip.value[0],current):
        offset = abs(i-j)
        offset_max = offset if offset > offset_max else offset_max

    time_slot = 1.5 + offset_max/speed*6.67
    self.send_angles(clip.value[0], speed)
    print(clip.name, time_slot)
    time.sleep(time_slot)


def cam_rotate(self, axis: str, angle: int, speed=60):
    """
    Rotate cobot's camera in 6 axis

    param : axis, uw-UpWards dw-DownWards lw-LeftWards rw-RightWards cw-ClockWise cc-CounterClock
    """
    # amendment for zero start, h-horizon v-vertical c-clockwise
    angles = self.get_angles()
    # print(angles)
    # return
    time_slot = 1 + abs(angle) / speed * 6.67
    # amendment = {"h": 0, "v": -100, "c": 142}  # +- 45
    axis = axis.lower()

    # degree [-145,-55]
    if axis == "v":
        cur_angle = angles[3] - angle * d2r
        cur_angle = cur_angle if cur_angle > -25.3068 else -25.3068
        cur_angle = cur_angle if cur_angle < -9.5991 else -9.5991
        print("v", cur_angle)
        self.send_angle(Angle.J4.value, cur_angle, speed)
    # degree [-45,45]
    elif axis == "h":
        cur_angle = angles[4] - angle * d2r
        cur_angle = cur_angle if cur_angle > -7.8538 else -7.8538
        cur_angle = cur_angle if cur_angle < 7.8538 else 7.8538
        print("h", cur_angle)
        self.send_angle(Angle.J5.value, cur_angle, speed)
    # degree [97,187]
    elif axis == "c":
        cur_angle = angles[5] - angle * d2r
        cur_angle = cur_angle if cur_angle > 16.9294 else 16.9294
        cur_angle = cur_angle if cur_angle < 32.6371 else 32.6371
        self.send_angle(Angle.J6.value, cur_angle, speed)

    time.sleep(time_slot)


def create(port=None):
    if not port:
        port = subprocess.check_output(['echo -n /dev/ttyUSB*'], shell=True).decode()
    print('::instance create')
    return MyCobot(port)


def free(self):
    print('::set_free_mode()')
    self.set_free_mode()


def customize():
    MyCobot.state = state
    MyCobot.create = create
    MyCobot.free = free
    MyCobot.cam_rotate = cam_rotate


def animation():
    customize()
    mycobot = MyCobot.create()
    mycobot.state(AngleAnimation.Start)
    mycobot.state(AngleAnimation.Prepare)
    mycobot.state(AngleAnimation.Observer)
    mycobot.cam_rotate("h", 15)
    mycobot.cam_rotate("h", -15)
    mycobot.cam_rotate("v", 25)
    mycobot.cam_rotate("c", 35)
    mycobot.state(AngleAnimation.Start)
    mycobot.free()


def locate(precision=0.1):
    customize()
    mycobot = MyCobot.create()
    # mycobot.state(cobot.AngleAnimation.Prepare)
    mycobot.state(AngleAnimation.Observer)


    cap = cv2.VideoCapture(0)
    for i in range(5):
        ret, frame = cap.read()
        # time.sleep(0.1)
    max_trials = 5000
    pre_dir = [0, 0]
    step = [10, 10]
    for i in range(max_trials):
        cap.release()
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cv2.imshow('frame2', frame)
        res = detect(frame, RED_RANGES, 0.3)
        if res:
            offset = [res[0] - 0.5, res[1] - 0.5]
            if offset[0] < precision and offset[1] < precision:
                break
            now_dir = [np.sign(offset[0]), np.sign(offset[1])]
            print("res", res,"offset", offset, "now dir", now_dir)
            if offset[0] > precision:
                print("!!!")
                if now_dir[0] + pre_dir[0] == 0:
                    print("sda")
                    step[0] /= 2
                mycobot.cam_rotate("v", now_dir[0] * step[0])
            # if offset[1] > precision:
            #     print("???")
            #     if now_dir[1] + pre_dir[1] == 0:
            #         step[1] /= 2
            #     mycobot.cam_rotate("h", now_dir[1] * step[1])
            pre_dir = now_dir
        # cv2.imwrite("result.jpg", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    # Our operations on the frame come here
    # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Display the resulting frame
    # cv2.imshow('frame', gray)

    # cv2.waitKey()
    cv2.destroyAllWindows()
    mycobot.state(AngleAnimation.Start)
    mycobot.free()


if __name__ == '__main__':

    # # mycobot.state(AngleAnimation.Start)
    # # mycobot.state(AngleAnimation.Prepare)
    # # mycobot.state(AngleAnimation.Observer)
    # mycobot.state(AngleAnimation.Start)
    # # mycobot.cam_rotate("cc", 30)
    # # print('==> degrees: {}\n'.format(mycobot.get_angles()))

    # customize()
    # mycobot = MyCobot.create()
    # mycobot.state(AngleAnimation.Observer)
    # mycobot.cam_rotate("h", 15)
    # mycobot.cam_rotate("h", 15)
    # mycobot.cam_rotate("v", 15)
    # mycobot.state(AngleAnimation.Start)
    # mycobot.free()

    locate()
