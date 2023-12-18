#!/usr/local/bin/python3 -S

import os
import sys
import time
import signal
import socket
from datetime import datetime
import getpass
import subprocess
import fcntl
import termios
import struct


# TODO change to your main username - when running as a different user, their username
# will show up in the prompt. When running as the primary user, it's not shown
# (so it doesn't take up space)
PRIMARY_USER = getpass.getuser()

# linux-utils cwd abbreviator
CWDABBR_EXE = os.environ.get("CWDABBR_EXE", os.path.expanduser("~/libexec/cwdabbr"))

STATE_UPDATE_INTERVAL_S = 1

STTY_EXE = "/usr/bin/stty"
GIT_EXE = "/usr/bin/git"

if not sys.argv[2:]:
    print(f"usage: {sys.argv[0]} fifo_ps1 fifo_rps1")
    sys.exit(1)

parent_pid = os.getppid()
parent_pid_cwdfile = f"/proc/{parent_pid}/cwd"
parent_tty = os.readlink(f"/proc/{parent_pid}/fd/0")

hostname = socket.gethostname().split(".")[0]
whoami = getpass.getuser()

# Prompt is of the form
#   {prefix}{cwdabbr}{suffix}
# Prefix and suffix won't change, so just calculate them once

# Format 1
# when user != primary user: [user@host cwd]$
# when user == primary user: [host cwd]$
if False:
    prompt_prefix = "%f%k["
    if whoami != PRIMARY_USER:
        prompt_prefix += f"%F{{red}}%B{whoami}%f%B@"
    else:
        prompt_prefix += "%B"
    prompt_prefix += f"{hostname}%b "
    prompt_suffix = "%f]%(!.#.$)"

# Format 2
# when user != primary user: user@host[cwd]:
# when user == primary user: host[cwd]:
if True:
    prompt_prefix = "%f%k"
    if whoami != PRIMARY_USER:
        prompt_prefix += f"%F{{red}}%B{whoami}%f%B@"
    else:
        prompt_prefix += "%B"
    prompt_prefix += f"{hostname}%b["
    prompt_suffix = "%f]:"


class State:
    term_cols = 0
    git_branch = ""
    datetime = ""
    cwd = ""
    cwd_abbr = ""

STATE = State()

def update_terminal_cols(pts):
    try:
        # ew. but it's the only thing I could get working.
        # Probably because of how shell redirections work.
        result = subprocess.run(f"{STTY_EXE} size < {pts}", shell=True, capture_output=True, text=True, check=True)
        rows, cols = map(int, result.stdout.split())
        STATE.term_cols = cols
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return 80

def git_get_branch():
    p = subprocess.Popen(
            [GIT_EXE, "symbolic-ref", "-q", "--short", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
    )
    stdout, _ = p.communicate()
    if p.returncode == 0:
        STATE.git_branch = stdout.strip()
        return

    p = subprocess.Popen(
            [GIT_EXE, "describe", "--tags", "--exact-match"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
    )
    stdout, _ = p.communicate()
    if p.returncode == 0:
        STATE.git_branch = stdout.strip()
    else:
        STATE.git_branch = ""

def update_datetime():
    STATE.datetime = datetime.now().strftime("%m/%d %H:%M")

def get_cwdabbr():
    cwd = os.readlink(parent_pid_cwdfile)
    if cwd != STATE.cwd:
        os.chdir(cwd)
        git_get_branch()
        STATE.cwd = cwd
        cols = STATE.term_cols
        if cols < 145:
            args = [CWDABBR_EXE, "--abbreviate", "--short"]
        else:
            args = [CWDABBR_EXE, "--abbreviate"]
        p = subprocess.Popen(args, stdout=subprocess.PIPE, text=True)
        stdout, _ = p.communicate()
        cwd_abbr = stdout.replace("$", "\\\\\\$")
        STATE.cwd_abbr = cwd_abbr
        return cwd_abbr
    else:
        return STATE.cwd_abbr

def update_state():
    update_terminal_cols(parent_tty)
    git_get_branch()
    update_datetime()

def write_prompt_to_fifo():
    cwdabbr = get_cwdabbr()
    prompt = f"{prompt_prefix}{cwdabbr}{prompt_suffix}"
    with open(sys.argv[1], "w") as fifo_ps1:
        fifo_ps1.write(prompt)

    right_prompt = ""
    if STATE.term_cols > 145:
        if STATE.git_branch:
            right_prompt += f"%F{{green}}[{STATE.git_branch}]%f "
        right_prompt += STATE.datetime

    with open(sys.argv[2], "w") as fifo_rps1:
        fifo_rps1.write(right_prompt)

signal.signal(signal.SIGUSR1, lambda *_: write_prompt_to_fifo())

update_state()
os.kill(parent_pid, signal.SIGUSR1)

while True:
    try:
        os.kill(parent_pid, 0)
    except OSError:
        print("-- Parent process died, exiting... ---")
        break
    update_state()
    time.sleep(STATE_UPDATE_INTERVAL_S)

