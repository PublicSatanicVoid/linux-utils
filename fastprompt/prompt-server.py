#!/usr/bin/env python3

import os
import sys
import time
import signal
import socket
import datetime


parent_pid = os.getppid()

hostname = socket.gethostname().split(".")[0]
whoami = os.getlogin()

def write_prompt_to_fifo():
    parent_cwd = os.readlink(f"/proc/{parent_pid}/cwd")

    datetimestr = datetime.datetime.now().strftime("%H:%M")

    with open(sys.argv[1], "w") as fifo:
        fifo.write(f"{datetimestr} [{whoami}@{hostname} {parent_cwd}] > ")

signal.signal(signal.SIGUSR1, lambda *_: write_prompt_to_fifo())
os.kill(parent_pid, signal.SIGUSR1)

while True:
    time.sleep(10)
