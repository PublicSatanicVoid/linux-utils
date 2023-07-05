#!/usr/local/bin/python3.11 -S
"""\
jumpto: Utility for labeling and recalling locations.

Useful for working on multiple projects in large filesystems where a
project may have relevant files in multiple disks.

Store one or more locations under a label with ``jumpto -s <label>``
and jump back to them with ``jumpto <label>`` (if there are multiple
locations, you are prompted to select which one.)
"""

import getpass
import os
import sys

__copyright__ = "Copyright (c) 2023 Broadcom Corporation. All rights reserved."
__license__ = "Public Domain"
__version__ = "1.0.0"

USER = getpass.getuser()
JUMP_LIST = f"/home/{USER}/.jump"
os.makedirs(JUMP_LIST, mode=0o755, exist_ok=True)

if "_JUMPTO" in os.environ:
    # We are being sourced through the Bash wrapper - good!
    IS_SOURCED = True
    DEST_HOLDER = os.environ["_JUMPTO"]
else:
    # We are not being sourced, so we have to use subshells to change
    # cwd
    IS_SOURCED = False
    SHELL = os.environ.get("SHELL", "/bin/bash")

if not sys.argv[1:]:
    print(f"jumpto [-s|-e|-d|-v] [label]")
    print("  -s: store cwd to jump label")
    print("  -e: edit a jump label")
    print("  -d: delete a jump label")
    print("  -v: view jump label")
    print("")

    labels = [
        label for label in os.listdir(JUMP_LIST) if not label.startswith(".nfs")
    ]
    if not labels:
        print("no jump labels found")
    else:
        print("labels:")
        maxlen = max((len(label) for label in labels), default=0)

        for label in sorted(labels):
            with open(f"{JUMP_LIST}/{label}", mode="r") as f:
                nlocs = len([line for line in f.readlines() if line.strip()])
            print(f"  {label.ljust(maxlen)}"
                  f"  ({nlocs} location{'s' if nlocs > 1 else ''})")

    sys.exit(0)

if sys.argv[1] == "-s":
    if not sys.argv[2:]:
        print(f"jumpto -s <label>")
        sys.exit(1)
    label = sys.argv[2]
    jumps = []
    if os.path.exists(f"{JUMP_LIST}/{label}"):
        with open(f"{JUMP_LIST}/{label}", mode="r") as f:
            jumps.extend(line.strip() for line in f.readlines())
    path = os.path.realpath(os.getcwd())
    if path in jumps:
        print(f"jumpto: path already stored to label '{label}': {path}")
        sys.exit(1)
    with open(f"{JUMP_LIST}/{label}", mode="a+") as f:
        f.write(os.path.realpath(os.getcwd()) + "\n")
    print(f"jumpto: stored path to label '{label}': {path}")
    sys.exit(0)

if sys.argv[1] == "-e":
    if not sys.argv[2:]:
        print(f"jumpto -e <label>")
        sys.exit(1)
    label = sys.argv[2]
    if not os.path.exists(f"{JUMP_LIST}/{label}"):
        print(f"jumpto: label '{label}' does not exist")
        sys.exit(1)
    os.system(f"vim '{JUMP_LIST}/{label}'")
    print(f"jumpto: label '{label}' edited and saved")
    sys.exit(0)

if sys.argv[1] == "-d":
    if not sys.argv[2:]:
        print(f"jumpto -d <label>")
        sys.exit(1)
    label = sys.argv[2]
    if not os.path.exists(f"{JUMP_LIST}/{label}"):
        print(f"jumpto: label '{label}' does not exist")
        sys.exit(1)
    os.remove(f"{JUMP_LIST}/{label}")
    print(f"jumpto: label '{label}' removed")
    sys.exit(0)

if sys.argv[1] == "-v":
    if not sys.argv[2:]:
        print(f"jumpto -v <label>")
        sys.exit(1)
    label = sys.argv[2]
    if not os.path.exists(f"{JUMP_LIST}/{label}"):
        print(f"jumpto: label '{label}' does not exist")
        sys.exit(1)
    with open(f"{JUMP_LIST}/{label}", mode="r") as f:
        jumps = [line.strip() for line in f.readlines() if line.strip()]
    for i, path in enumerate(jumps, 1):
        flag = ""
        if not os.path.exists(path):
            flag = "[no longer exists]"
        print(f"  {i}: {path} {flag}")
    sys.exit(0)

label = sys.argv[1]
if not os.path.exists(f"{JUMP_LIST}/{label}"):
    print(f"jumpto: label '{label}' does not exist")
    sys.exit(1)
with open(f"{JUMP_LIST}/{label}", mode="r") as f:
    jumps = [line.strip() for line in f.readlines()]
    if len(jumps) == 1:
        jump_to = jumps[0]
    else:
        print(f"jumpto: multiple locations defined for label '{label}'")
        print("enter the number of the location to jump to: ")
        for i, path in enumerate(jumps, 1):
            flag = ""
            if not os.path.exists(path):
                flag = "[no longer exists]"
            print(f"  {i}: {path} {flag}")
        try:
            num = int(input())
        except KeyboardInterrupt:
            print("\nCtrl+C received, exiting")
            sys.exit(1)
        if num < 1 or num > len(jumps):
            print(f"jumpto: invalid number '{num}'")
            sys.exit(1)
        jump_to = jumps[num - 1]

    if IS_SOURCED:
        with open(DEST_HOLDER, "w+") as f:
            f.write(jump_to)
    else:
        os.chdir(jump_to)
        os.system(SHELL)
