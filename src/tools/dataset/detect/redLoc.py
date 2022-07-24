import pandas
import cv2

file_src = r'C:\Users\JC\Desktop\CLickSeg\img'    # 数据存储目录
img_back = '.png'
img_nums = 32   

stand_px = 2.3   # 以 1920*1080 在小车轨道固定高度计算的

save_file = r'C:\Users\JC\Desktop\CLickSeg\mouse_loc.csv' # n数据存储文件

# data mode: 'xxxx':[[center_offset_l:[(x-c_l)/stand_px], center_offset_w:[(y-c_w)/stand_px]]]
mouse_loc = {}

overlaped = (1080/stand_px - 320)/(1080/stand_px)/2

def loc2real(x, y, img):
    w, l = img.shape[0:2]
    c_w, c_l = w/2.0,l/2.0  # 转换坐标轴位置
    # print(c_w, c_l)
    return (x-c_l)/stand_px, (y-c_w)/stand_px   # 坐标转换后 将px转换为mm

def check_mouse_loc(event, x, y, flags, param):
    # 窗口中鼠标左键的"按下"事件回调
    if event == cv2.EVENT_LBUTTONDOWN:
        # [realmm_x, realmm_y]
        mouse_loc[param[0]].append([*loc2real(x, -y, img)])

if __name__ == '__main__':
    cv2.namedWindow('image')
    for num in range(img_nums):
        
        # 生成图片名字，命名规则为: 0xx.png, 例: 000.png 001.png
        zero = ''.join(['0' for i in range(max(0, 3-len(str(num))))])
        img_nam = '/{0:s}'.format(zero+str(num))

        # 初始化坐标字典数据
        mouse_loc[img_nam[1:]] = []
        # 读取图片
        img = cv2.imread(file_src+img_nam+img_back, cv2.IMREAD_COLOR)
        
        y1 = int(overlaped * img.shape[0])
        y2 = int((1-overlaped) * img.shape[0])
        cv2.line(img, (0,y1), (img.shape[1],y1),(255,0,0), 3) 
        cv2.line(img, (0,y2), (img.shape[1],y2), (255,0,0), 3) 
        
        cv2.resizeWindow('image', img.shape[1], img.shape[0])
        # mouse_loc[img_nam[1:]].append([img.shape[0]/2.0, img.shape[1]/2.0])
        cv2.setMouseCallback('image', check_mouse_loc, [img_nam[1:], img])
        
        cv2.imshow('image',img)
        
        # 监听输入状态: n-下一张 q-结束 others-无反应
        flag = 1
        while flag:
            key = cv2.waitKey(0)
            if key & 0xFF == 110:
                print('next')
                flag = 2
                break
            elif key & 0xFF == 113:
                print('over')
                flag = 0
                break
            else: 
                continue
        if flag:
            print(img_nam[1:]+":",mouse_loc[img_nam[1:]])
            continue
        else:
            break

    # 数据存储
    lis = pandas.DataFrame()
    for key in mouse_loc:
        # 罪魁祸首
        """ if len(mouse_loc[key]) < 2:
            continue """
        lis = pandas.concat([lis, pandas.Series({key:mouse_loc[key]})])
    # lis.columns = ['img_num']
    lis.to_csv(save_file, index_label=False,header=False)
