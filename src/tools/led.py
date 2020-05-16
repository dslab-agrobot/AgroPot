import argparse
import board
import neopixel
import time
from enum import Enum

#  proc = subprocess.Popen(['sudo','python3','/home/pi/led.py', 'on_r']) print("****", debug)
# GIPO use BCM Position


class Color(Enum):
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    WHITE = (255, 255, 255)


def rainbow():
    colors = [[207, 19, 28], [243, 151, 41], [247, 236, 0], [114, 187, 64]
        , [0, 158, 80], [0, 172, 179], [0, 153, 222], [44, 75, 158]]
    pixels = neopixel.NeoPixel(board.D18, 8)

    mid_p = 0
    while True:
        if mid_p >= 8:
            mid_p = 0
        for i in range(8):
            now_p = mid_p + i if (mid_p + i) < 7 else (mid_p + i - 8)
            pixels[i] = colors[now_p]
        mid_p += 1
        time.sleep(0.25)


def light_off():
    pixels = neopixel.NeoPixel(board.D18, 8)
    pixels.fill((0, 0, 0))
    pixels.show()


def light_on(color: Color):
    pixels = neopixel.NeoPixel(board.D18, 8)
    pixels.fill(color.value)
    pixels.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", help="(On of OFF)_(Color) like on_r off ", type=str)
    args = parser.parse_args().cmd.strip().split('_')

    print("|", args[0], "|")

    if args[0] == "off":
        light_off()
    else:
        if args[1] == "r":
            light_on(Color.RED)
        elif args[1] == "g":
            light_on(Color.GREEN)
        elif args[1] == "w":
            light_on(Color.WHITE)
