#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Navigator to control robot to move and act
__copyright__="Jiangxt"
__email__ = "<jiangxt404@qq.com>"
__license__ = "GPL V3"
__version__ = "0.1"

"""

import canMsgHandler as can
from multiprocessing import Process,JoinableQueue

class Navigator(object):
    
    CAN_SUV_FG = True	

    """
    Navigator to control the robot
    
    1) Suveillance of the can devices
    2)
    """

    def update(self):
        pass    
