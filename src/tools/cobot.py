import time, random, subprocess
from enum import Enum
from pymycobot.mycobot import MyCobot
from pymycobot.genre import Angle, Coord
from detector import *
import numpy as np
import argparse
from math import sin, cos, pi

# degree to radian
d2r = 0.17453

# correction angle and pos for observation
cor_angle = [-79.64246834355126, 0.0, -89.95588151034207]
cor_pos = [-240.5, +64.6, -226.8]


class AngleAnimation(Enum):
    Start = [15.9, -24.91, -26.66, -26.79, -14.23, 31.41],
    Prepare = [0, -24, -26, -2.5, 0, 31.41],
    Observer = [0, 15, 0, -16.8, 0, 31.41],


class RobotArm(MyCobot):
    def __init__(self, port=None):
        if not port:
            port = subprocess.check_output(['echo -n /dev/ttyUSB*'], shell=True).decode()
        super().__init__(port)
        print('Instance create on device %s' % port)

    def state(self, clip: AngleAnimation, speed=70):
        current = self.get_angles()
        offset_max = 0
        for i, j in zip(clip.value[0], current):
            offset = abs(i - j)
            offset_max = offset if offset > offset_max else offset_max

        time_slot = 1.5 + offset_max / speed * 6.67
        self.send_angles(clip.value[0], speed)
        print(clip.name, time_slot)
        time.sleep(time_slot)

    def cam_rotate(self, axis: str, angle: int, speed=60):
        """
        Rotate cobot's camera in 6 axis

        param : axis, v-vertical(default up), h-horizontal(default right)
            c-ClockWise
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
            cur_angle = angles[4] + angle * d2r
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

    def get_tool_head(self):
        """
        Return the position and angle of tools head
        Pos[X,Y,X] Angle[rx,ry,rz]

        There are the inf for agrobot
        return: Pos   [bot+/up-, right+/left-, bac+/font-]
        return: Angle [font+/bac-, rotate, right+/left-]
        """
        tool_pos = np.array(self.get_coords()[:3]) + cor_pos
        tool_angle = np.array(self.get_coords()[3:])/d2r + cor_angle

        return tool_pos, tool_angle

    def get_movement(self, estimated_length):
        k = pi/180
        pos, angle = self.get_tool_head()
        alpha = angle[0] * k  # Angle for front
        beta = angle[2] * k  # Angle for right
        move_x = estimated_length * cos(beta) * sin(alpha)
        move_z = estimated_length * cos(alpha) * cos(beta)
        move_y = estimated_length * cos(alpha) * sin(beta)

        print(move_x, move_y, move_z)
        return move_x, move_y, move_z

    def locate(self, precision=0.05, color_ranges=GREEN_RANGES, min_r=0.05):

        max_trials = 5000
        pre_dir = [0, 0]
        step = [5, 5]
        for i in range(max_trials):
            print("\nTrail %d" % i)
            frame = camera_capture()
            res, c_img = detect(img=frame, hsv_ranges=color_ranges, min_r=min_r,
                                debug=True)
            # cv2.imshow('vision', frame)
            # cv2.waitKey(0)
            if res:
                offset = [abs(res[0]), abs(res[1])]
                now_dir = [np.sign(res[0]), np.sign(res[1])]
                # print("Position X: %3.2f Y: %3.2f" % (res[0], res[1]))

                if abs(offset[0]) < precision and abs(offset[1]) < precision:
                    dis = distance_estimate(res[2])
                    print("radius %d, distance %d" % (res[2], dis))
                    movement = self.get_movement(dis)
                    print("\nResult: \n", movement)
                    print("Located ! !")
                    return movement

                if offset[0] > precision:
                    # print("Horizon adjust")
                    if now_dir[0] + pre_dir[0] == 0:
                        # print("Horizon over rotated")
                        step[0] /= 2
                    # print("Horizon rotate", now_dir[0] * step[0])
                    self.cam_rotate("h", now_dir[0] * step[0])
                if offset[1] > precision:
                    # print("Vertical adjust")
                    if now_dir[1] + pre_dir[1] == 0:
                        # print("Vertical over rotated")
                        step[1] /= 2
                    # print("Vertical rotate", now_dir[1] * step[1])
                    self.cam_rotate("v", now_dir[1] * step[1])
                pre_dir = now_dir
                # cv2.destroyAllWindows()
            return None

    def free(self):
        print('::set_free_mode()')
        self.release_all_servos()


def animation():
    mycobot = RobotArm()
    mycobot.state(AngleAnimation.Start)
    mycobot.state(AngleAnimation.Prepare)
    mycobot.state(AngleAnimation.Observer)
    mycobot.cam_rotate("h", 15)
    mycobot.cam_rotate("h", -15)
    mycobot.cam_rotate("v", 25)
    mycobot.cam_rotate("c", 35)
    mycobot.state(AngleAnimation.Start)
    mycobot.free()


def camera_capture():
    cap = cv2.VideoCapture(0)
    for i in range(5):
        cap.read()
        # time.sleep(0.01)
    cap.release()
    ret, frame = cap.read()
    return frame


def locate_5dir():
    mycobot = RobotArm()
    # step1 Move Z to top level

    # step2 rotate camera and locate the ball
    args_list = [None, ["h", 15], ["h", -30], ["V", 15], ["h", -30]]
    for arg in args_list:
        if arg:
            print("Camera rotate", arg)
            mycobot.cam_rotate(arg[0], arg[1])
        movement = mycobot.locate(precision=0.05, color_ranges=GREEN_RANGES, min_r=0.02)
        print("Located:\nFront: %.2f cm, Right: %.2fcm, Down: %.2fcm" % (movement[0], movement[1], movement[2]))
        if movement:
            delta_x = int(movement[0] * 10)
            delta_y = int(movement[1] * 10)
            delta_z = int(movement[2] * 10)
            for d, n in [["X", delta_x], ["Y", delta_y],
                         ["Z", delta_z]]:
                if n > 40:
                    print("Robot move %s %dmm:" % (d, n))
            # step3 state to observer and locate again
            mycobot.state(AngleAnimation.Observer)
            mycobot.locate(precision=0.05, color_ranges=GREEN_RANGES, min_r=0.02)
            break


def locate_forward():
    mycobot = RobotArm()
    mycobot.state(AngleAnimation.Observer)
    try:
        mycobot.locate()
    except KeyboardInterrupt:
        print("terminated")
    finally:
        mycobot.state(AngleAnimation.Start)
        mycobot.free()


def un_freeze():
    mycobot = RobotArm()
    mycobot.free()


def freeze():

    mycobot = RobotArm()
    pos = mycobot.get_angles()
    mycobot.send_angles(pos, 10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("act", help="action", type=str)
    args = parser.parse_args()

    args.act = str(args.act).upper()
    if args.act == "F":
        freeze()
    elif args.act == "U":
        un_freeze()
    elif args.act == "LD":
        locate_5dir()
    elif args.act == "L":
        locate_forward()


    # un_freeze()

    # locate_forward()

