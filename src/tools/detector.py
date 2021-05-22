import time, cv2
import numpy as np

GREEN_RANGES = np.array([
    [[35, 55, 55], [95, 255, 255]]
])
YELLOW_RANGES = np.array([
    [[11, 55, 55], [34, 255, 255]]
])
RED_RANGES = np.array([
    [[0, 43, 43], [10, 255, 255]],
    [[156, 43, 43], [180, 255, 255]]
])

# radius of ball: 6.6 cm
# Distance = Radius x focus / pixels
RF = [
    # 10     20     30     40     50     60     70     80     90    100    110   cm
    # 366    244    193    142    114    98     79     67     59     53     48   pixel
    3660,    4880,  5790,  5680,  5700,  5880,  5530,  5360,  5310,  5300,  5280
]
Pixels = [
    366, 244, 193, 142, 114, 98, 79, 67, 59, 53, 48
]


def distance_estimate(pix):
    max_num = Pixels.__len__()
    rf = 0
    for i in range(max_num):
        if pix == Pixels[i]:
            rf = RF[i]
            break
        if pix < Pixels[i]:
            if i + 1 < max_num:
                continue
            else:  # last element
                rf = RF[i]
                break
        else:
            if i == 0:
                rf = RF[0]
            else:
                k1 = (pix - Pixels[i]) / (Pixels[i - 1] - Pixels[i])
                k2 = 1 - k1
                rf = int(RF[i - 1] * k1 + RF[i] * k2)
                break
    return int(rf / pix)


def detect(img, hsv_ranges, min_r=0.35, debug=False):
    # print(img.shape)
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask0 = np.zeros((img_hsv.shape[0], img_hsv.shape[1]), dtype=np.uint8)
    for r in hsv_ranges:
        mask0 = cv2.bitwise_or(mask0, cv2.inRange(img_hsv, r[0], r[1]))

    # cv2.imshow("Ranged", cv2.bitwise_and(img, img, mask=mask0))
    new_size = tuple((1 / img.shape[0] * 512.0 * np.array(img.shape[:2])).astype(int))
    # print(new_size,img.shape[:2])
    white = 255 * np.ones(img.shape[:2])
    masked_white = cv2.bitwise_and(white, white, mask=mask0)
    # cv2.imwrite("mask0.png", masked_white)
    masked_white = cv2.resize(masked_white, new_size[::-1], interpolation=cv2.INTER_AREA)

    # Remove dot
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    opened = cv2.morphologyEx(masked_white, cv2.MORPH_OPEN, kernel, iterations=2)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=10)

    closed = closed.astype(np.uint8)
    closed = cv2.cvtColor(closed, cv2.COLOR_GRAY2RGB)
    mask1 = cv2.inRange(closed, np.array([10, 10, 10]), np.array([255, 255, 255]))
    mask1 = cv2.resize(mask1, img.shape[:2][::-1], interpolation=cv2.INTER_AREA)
    # cv2.imwrite("mask1.png", mask1)
    img_p = cv2.bitwise_and(img, img, mask=mask1)
    contours, hierarchy = cv2.findContours(mask1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # cnt = contours[4]

    if contours.__len__() == 0:
        return None, None
    # print(contours)
    c_img = cv2.drawContours(img, contours, -1, (0, 255, 0), 3)
    result = []
    radius_max = 0
    circle_para = []
    for ct in contours:
        (x, y), radius = cv2.minEnclosingCircle(ct)
        if radius > radius_max and radius > min_r * img.shape[0]:
            radius_max = radius
            result = [x / img.shape[1] - 0.5, 0.5 - y / img.shape[0], radius]
            circle_para = [(int(x), int(y)), int(radius_max)]
            # print(x,y)
        # print(np.mean(ct, axis=0))
    if circle_para and debug:
        c_img = cv2.circle(c_img, circle_para[0], circle_para[1], (255, 0, 0), 2)
        c_img = cv2.circle(c_img, circle_para[0], 5, (255, 255, 255), 4)
        c_img = cv2.line(c_img, (int(img.shape[1] / 2), 0), (int(img.shape[1] / 2), int(img.shape[0])),
                         (0, 0, 255), 2)
        c_img = cv2.line(c_img, (0, int(img.shape[0] / 2)), (int(img.shape[1]), int(img.shape[0] / 2)),
                         (0, 0, 255), 2)
    cv2.imwrite("counter.png", c_img)
    # cv2.imwrite("counter.png", c_img)
    # cv2.waitKey()
    return result, c_img


# img_path = 'C:/Users/JC/Desktop/f_t1.jpg'
# img = cv2.imread(img_path)
# print(detect(img, GREEN_RANGES))
# data_mask('C:/Users/JC/Desktop/f_t1.jpg')

# print(distance_estimate(79))
