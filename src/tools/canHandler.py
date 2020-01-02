#! /usr/bin/python

import time
import os
import logging
import daemon


ACTIVATE = True


def child_process():
    logging.info("PID: %d" % os.getpid())
    while ACTIVATE:
        logging.info("fkg.")
        time.sleep(1)


def main():
    with daemon.DaemonContext():
        logging.basicConfig(filename='D:/mylog.log', level=logging.INFO)
        child_process()


if __name__ == '__main__':
    main()
