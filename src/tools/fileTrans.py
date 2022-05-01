import os

os.popen('scp -r /home/pi/data/* agrobot@192.168.50.50:/home/agrobot/data')

os.popen('rm -rf /home/pi/data/*')

