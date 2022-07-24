import numpy as np
import pandas as pd 
import json
import os 
from os.path import join as pj
import pickle
_cur_path = os.path.dirname(os.path.abspath(__file__))

# DATA SETTINGS
# The robot moves 320mm per step, totally 32 steps. (10.24 meters)
# The camera captures 1980*1080 per frame, about 23px=1cm.


# Get root pos by clicking on the monitor
_manual_data_path = r'/home/pi/AgroPot/src/tools/dataset/detect/mouse_loc.csv'

# Get root pos by red pieces
_red_data_path = r''

# TBD
camera_effctor_distance = 800

root_data_path = _manual_data_path

def imgLoc2Coord(img_dir=1):
    """Coord in images to real
    
    img_dir: 1 for South-North, -1 for the opposite.
    """
    
    df = pd.read_csv(root_data_path,index_col=False,header=None)
    cords=[]
    for i, row in df.iterrows():
        img_idx, locs = int(row[0]),json.loads(row[1])
        if len(locs) == 0:
            continue
        for loc in locs :
            y = -round(loc[0],2)
            # TBD calc Y Range
            # MAX Y 700 mm
            if y > 300:
                y = 300
            elif y < -300:
                y = -300
            if img_dir == 1:
                x=round(img_idx*320+ loc[1],2) + camera_effctor_distance
                cords.append([x,y])
            elif img_dir == -1:
                x=round(10240 - img_idx*320+ loc[1],2) + camera_effctor_distance
                cords.insert(0,[x,y])
    cords = np.array(cords)
    cords = cords[cords[:, 0].argsort()]
    f=open(pj(_cur_path, "coord.pk"),"wb")
    pickle.dump(cords, f)
    f.close()
    
  
def getLoc():
    f=open(pj(_cur_path, "coord.pk"),"rb")
    cords = pickle.load(f)
    f.close()
    return cords
        
if __name__ == "__main__":
    imgLoc2Coord()
    print(getLoc())












