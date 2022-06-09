import cv2
from os.path import join as pj
import numpy as np
from os import listdir
from os.path import isfile

PIX_PER_MM = 2.3

def list_files(mypath):
    return [f for f in listdir(mypath) if isfile(pj(mypath, f))]

def list_folders(mypath):
    return [f for f in listdir(mypath) if not isfile(pj(mypath, f))]

def green_cord(img, min_area = 600, max_area = 9e20, draw=False, k=1.1):
    """
    Extract all plant-lile part form given image. Ignore tiny ones, and merge close ones.
    
    @param img: image BGR
    @param min_area: min size to ignore, default 600 is about 1 cm^2
    @param max_area: max size to ignore
    @param draw: if to draw bounding box on masked image
    @param k: ratio of neighboring blocks to merge

    @return out: bounding box coords [x,y,w,h]
    @return img_green: background masked image
    """ 
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # green parameters
    lower_green =  np.array([30,33,33])

    higher_green = np.array([80,255,255])


    mask = cv2.inRange(hsv, lower_green, higher_green)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(3, 3))


    opened = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel,iterations=3)

    
    img_green = cv2.bitwise_and(img, img, mask = opened)

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
            if i==j:
                if i == 0 and crd_length==0:
                    # print('??')
                    out.append(Coordinates_list[i])
                continue
            # print(i,j)
            
            # if i == j == 0 and crd_length==0:
            #     print('??')
            #     out.append(Coordinates_list[i])
            #     continue
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

def test(record_path):
    record_path = "/home/pi/20220501-1000"
    out_root = "/home/pi/AgroPot/src/tools/dataset"
    names = list_files(record_path)
    
    for idx,n in enumerate(names):
        img = cv2.imread(pj(record_path,n))
        # print(img.shape)
        # exit()
        coors, img_out = green_cord(img)
        if len(coors)==0:
            continue
        print(len(coors))
        for i,c in enumerate(coors):
            img_cut = img_out[c[1]:c[1]+c[3], c[0]:c[0]+c[2],:]
            cv2.imwrite(pj(out_root,"%2d-%2d.png")%(idx,i), img_cut)
            
            
        vis = np.concatenate((img, img_out), axis=1)
        cv2.imwrite(pj(out_root, "%02d.png"%idx),vis)
        # print(coor)
        # return
        print(idx, "*"*10)
        # exit()
        
    
    


if __name__ == "__main__":
    # img = camera_capture()
    # cv2.imwrite("2.png", img)
    
    test("?")
# 23pix per cm  