import os,subprocess

# os.popen('scp -r /home/pi/data/* agrobot@192.168.50.50:/home/agrobot/data/ori/')

# os.popen('rm -rf /home/pi/data/*')

subprocess.Popen('scp -r /home/pi/data/* agrobot@192.168.50.50:/home/agrobot/data/ori/', shell=True).wait()
subprocess.Popen('rm -rf /home/pi/data/*', shell=True).wait()
