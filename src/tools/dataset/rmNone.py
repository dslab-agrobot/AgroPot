
from os.path import join as pj
from os import listdir
from os.path import isfile, isdir
import sys
import shutil


# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, r'/home/jiangxt21/Project/CrackDetection/data')


def list_files(_path):
    return [f for f in listdir(_path) if isfile(pj(_path, f))]

def list_folders(_path):
    return [f for f in listdir(_path) if isdir(pj(_path, f))]

_root = "/home/pi/data"

fds = list_folders(_root)

for fd in fds:
    files = list_files(pj(_root,fd))
    if len(files)==0:
        shutil.rmtree(pj(_root,fd))
