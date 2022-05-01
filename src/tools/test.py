import numpy as np
import cv2
import time
from detector import *


def locate(precision=0.05):
    cap = cv2.VideoCapture(0)
    for i in range(5):
        ret, frame = cap.read()
        time.sleep(0.1)
    max_trials = 5000
    pre_dir = [0, 0]
    step = [5, 5]
    for i in range(max_trials):
        cap.release()
        cap = cv2.VideoCapture(0)
        print("Trail %d" % i)
        ret, frame = cap.read()
        res, c_img = detect(img=frame, hsv_ranges=GREEN_RANGES, min_r=0.1,
                            debug=True)
        # cv2.imshow('vision', frame)
        # cv2.waitKey(0)
        _ = input()
        if res:
            offset = [abs(res[0]), abs(res[1])]
            now_dir = [np.sign(res[0]), np.sign(res[1])]

            print("Position X: %3.2f Y: %3.2f, R: %d" % (res[0], res[1], res[2]))

            if abs(offset[0]) < precision and abs(offset[1]) < precision:
                print("Located ! !")
                # break

            if offset[0] > precision:
                print("Horizon adjust")
                if now_dir[0] + pre_dir[0] == 0:
                    print("Horizon over rotated")
                    step[0] /= 2
                print("Horizon rotate", now_dir[0] * step[0])

            if offset[1] > precision:
                print("Vertical adjust")
                if now_dir[1] + pre_dir[1] == 0:
                    print("Vertical over rotated")
                    step[1] /= 2
                print("Vertical rotate", now_dir[1] * step[1])
            pre_dir = now_dir
        # cv2.imwrite("result.jpg", frame)
        # cv2.destroyAllWindows()
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break
    # Our operations on the frame come here
    # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Display the resulting frame
    # cv2.imshow('frame', gray)

    # cv2.waitKey()
    # cv2.destroyAllWindows()


if __name__ == "__main__":
    locate()


