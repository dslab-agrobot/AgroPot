import time, cv2
import os,sys
from os.path import join as pj
import numpy as np
from os import listdir,mkdir
from os.path import isfile,exists

def list_files(mypath):
    return [f for f in listdir(mypath) if isfile(pj(mypath, f))]

def list_folders(mypath):
    return [f for f in listdir(mypath) if not isfile(pj(mypath, f))]


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

def camera_capture(cfg = [0, 1920, 1080]):
    """
    Args:
        cfg: [0, 1920, 1080] [2, 640, 480]
    
    """
    # {"next_dir": 1, "F": 0.0, "X": 200.0, "Y": 390.0, "Z": 310.0}
    # [0, 1920, 1080] [2, 640, 480]
    # 0 4K camera
    # 2 logi camera
    for i in range(10):
        cap = cv2.VideoCapture(cfg[0])
        cap.set(3, cfg[1])
        cap.set(4, cfg[2])
        for i in range(5):
            cap.read()
            time.sleep(0.01)
        ret, frame = cap.read()
        cap.release()
        if frame is None or frame.size == 0:
            print("Empty image captured, retrying %d"%i)
            os.system("usbreset")
            continue
        else:
            return frame
    raise Exception("USB camera at %d dead"%cfg[0])
    # raise Warning("USB camera at %d dead"%cfg[0])

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

def canny(image):
    t = 80
    canny_output = cv2.Canny(image, t, t * 2)
    return canny_output

def green_cord(img, min_area = 600, max_area = 9e20, draw=False, k=1.1): 
    out_root = "/home/pi/AgroPot/src/tools/"

        
    #file_name为提取图片路径，  area_avg为图片轮廓平均大小
    
    # img = cv2.imread(file_name) 
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # green parameters
    lower_green =  np.array([30,33,33])

    higher_green = np.array([80,255,255])


    mask = cv2.inRange(hsv, lower_green, higher_green)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(3, 3))


    opened = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel,iterations=3)

    
    img_green = cv2.bitwise_and(img, img, mask = opened)
    # img_green = cv2.bitwise_and(img, img, mask = mask)



    # binary = canny(img_green)
    # k = np.ones((3, 3), dtype = np.uint8)
    # binary = cv2.morphologyEx(binary, cv2.MORPH_DILATE, k)

    contours, hierarchy = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    Coordinates_list = []
    for c in range(len(contours)):
        area = cv2.contourArea(contours[c], False)
        if min_area < area < max_area: 
            x,y,w,h = cv2.boundingRect(contours[c])
            # Coordinates_list.append([[x,y],[x+w,y+h]]) # append bounding box
            Coordinates_list.append([x,y,w,h]) # append params
        else:
            x,y,w,h = cv2.boundingRect(contours[c])
            cv2.rectangle(img_green, (x, y), (x+w,y+h), (0, 0, 0), thickness=-1)
    
    # merge neighbor counters
    out=[] 
    crd_length = len(Coordinates_list)
    for i in range(crd_length):
        for j in range(i,crd_length):
            if i == j:
                if i == 0:
                    out.append(Coordinates_list[i])
                continue
            c1=Coordinates_list[i]
            c2=Coordinates_list[j]
            # (x1 -x2 +(w1-w2)/2) < 1/k(w1 + w2)
            if abs(c1[0] - c2[0] + (c1[2] -c2[2])/2)< (c1[2] +c2[2])/k and abs(c1[1] - c2[1] + (c1[3] -c2[3])/2)< (c1[3] +c2[3])/k:
                # print("combine")
                x00, y00, x01, y01 = c1[0], c1[1], c1[0]+c1[2], c1[1] + c1[3]
                x10, y10, x11, y11 = c2[0], c2[1], c2[0]+c2[2], c2[1] + c2[3]
                x0 = x00 if x00<x10 else x10
                y0 = y00 if y00<y10 else y10
                x1 = x01 if x01>x11 else x11
                y1 = y01 if y01>y11 else y11
                out.append([x0,y0,x1-x0,y1-y0])
                if c1 in out:
                    out.remove(c1)
                if c2 in out:
                    out.remove(c2)
                # print(x0,y0,x1,y1)
                # c_merge = 
            else:
                # print(c1,c2,abs(c1[0] - c2[0] + (c1[2] -c2[2])/2), (c1[2] +c2[2])/k , abs(c1[1] - c2[1] + (c1[3] -c2[3])/2), (c1[3] +c2[3])/k)
                # print("no change")
                out.append(c1)
                out.append(c2)
                
    if draw:
        for x,y,w,h in out:
            cv2.rectangle(img_green,(x,y),(x+w,y+h),(0,255,0),2) 
            text ="%d,%d"%(x,y)
            h_max, w_max= img_green.shape[:2]

            if y<0.1*h_max:
                # 25 is offset by 1080x1980
                cv2.putText(img_green,text,(x,y+h+25),cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255),2, cv2.LINE_AA)
            else:
                cv2.putText(img_green,text,(x,y),cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255),2, cv2.LINE_AA)       

    return  out, img_green

def test():
    for i in range(10000):
        # print("Try image at %d"%i)
        img = camera_capture()
        try:
            cv2.imwrite("0.png",img)
        except Exception as e:
            print(e, "Try image at %d"%i)
    


if __name__ == "__main__":
    # img = camera_capture()
    # cv2.imwrite("2.png", img)
    
    test()
# 23pix per cm  
  
# img_path = 'C:/Users/JC/Desktop/f_t1.jpg'
# img = cv2.imread(img_path)
# print(detect(img, GREEN_RANGES))
# data_mask('C:/Users/JC/Desktop/f_t1.jpg')

# print(distance_estimate(79))
