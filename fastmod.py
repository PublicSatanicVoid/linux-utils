#!/usr/local/bin/python3.11 -S
"""\
fastmod: Multithreaded utility for recursively changing permissions.

Runs as a standalone script.
"""

import getpass
import grp
import os
import multiprocessing as mp
import pwd
import shutil
import subprocess
import sys
import time

__copyright__ = "Copyright (c) 2023 Broadcom Corporation. All rights reserved."
__license__ = "Public Domain"
__version__ = "2.0.1"

# Logs chmod/chgrp commands and checks their return status.
DEBUG = False

# How many files to change per chmod/chgrp command.
DEFAULT_BLOCKSIZE = int(os.environ.get("FASTMOD_BLOCKSIZE", 128))

# How many worker processes to create.
DEFAULT_CORES = int(os.environ.get("FASTMOD_CORES", os.cpu_count() - 1))

# Preset to use if no flag or preset is specified.
DEFAULT_PRESET = os.environ.get("FASTMOD_PRESET", "umask")


def get_umask_str():
    """Returns the user's umask as a chmod-style string."""
    umask_exe = shutil.which("umask")
    umask_cmd = subprocess.Popen([umask_exe, "-S"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 text=True)
    umask, _ = umask_cmd.communicate()
    return umask.strip()


def calculate_umask_modifier(umask_str):
    """Calculates the changes to file and folder permissions for the given
    umask.
    
    Never add the executable bit to a file due to the umask.
    """
    mod_str_fil = ""
    mod_str_dir = ""
    for group in umask_str.split(","):
        add = []
        rem = []
        sel, perms = group.split("=")
        (add if "r" in perms else rem).append("r")
        (add if "w" in perms else rem).append("w")
        (add if "x" in perms else rem).append("x")
        add_fil = [p for p in add if p != "x"]
        add_dir = add
        rem_fil = rem_dir = rem
        if mod_str_fil:
            mod_str_fil += ","
            mod_str_dir += ","
        mod_str_fil += sel
        mod_str_dir += sel
        if add_fil:
            mod_str_fil += "+" + "".join(add_fil)
        if rem_fil:
            mod_str_fil += "-" + "".join(rem_dir)
        if add_dir:
            mod_str_dir += "+" + "".join(add_dir)
        if rem_dir:
            mod_str_dir += "-" + "".join(rem_dir)
    return mod_str_fil, mod_str_dir


def _test_calculate_umask_modifier():
    assert calculate_umask_modifier("u=rwx,g=rwx,o=rwx") == (
        "u+rw,g+rw,o+rw", "u+rwx,g+rwx,o+rwx")
    assert calculate_umask_modifier("u=rwx,g=rx,o=") == ("u+rw,g+r-w,o-rwx",
                                                         "u+rwx,g+rx-w,o-rwx")
    assert calculate_umask_modifier("u=rx,g=rx,o=") == ("u+r-w,g+r-w,o-rwx",
                                                        "u+rx-w,g+rx-w,o-rwx")
    assert calculate_umask_modifier("u=,g=,o=") == ("u-rwx,g-rwx,o-rwx",
                                                    "u-rwx,g-rwx,o-rwx")
    assert calculate_umask_modifier("u=rw,g=rw,o=r") == (
        "u+rw-x,g+rw-x,o+r-wx", "u+rw-x,g+rw-x,o+r-wx")


_test_calculate_umask_modifier()

_umask_fil, _umask_dir = calculate_umask_modifier(get_umask_str())

PRESETS = {
    "baseline": {
        "fil": "u+rw,g+r-w,o+r-w",
        "dir": "u+rwx,g+rxs-w,o+rx-w"
    },
    "group-allowed": {
        "fil": "ug+rw,o+r-w",
        "dir": "ug+rwx,g+s,o+rx-w"
    },
    "private": {
        "fil": "u+rw,go-rwx",
        "dir": "u+rwx,go-rwx"
    },
    "private-group": {
        "fil": "ug+rw,o-rwx",
        "dir": "ug+rwx,g+s,o-rwx"
    },
    "readonly": {
        "fil": "a-w,+t",
        "dir": "a-w,+t"
    },
    "umask": {
        "fil": _umask_fil,
        "dir": _umask_dir
    }
}

PRIMARY_GROUP = grp.getgrgid(pwd.getpwnam(getpass.getuser()).pw_gid).gr_name

if DEBUG:
    # DEBUG WRAPPER FOR TESTING
    _real_system = os.system
    def wrapped_system(cmd):
        print(os.getpid(), cmd)
        ret = _real_system(cmd)
        if ret != 0:
            print(f"ERROR :: {cmd} failed with exit code {ret}")
    os.system = wrapped_system


def worker_main(queue, group, quiet, blocksize, nontrivial):
    """Entry point for worker process."""
    buffer = {}
    if quiet:
        chmod = "chmod -f"
        chgrp = f"chgrp -f {group}"
    else:
        chmod = "chmod"
        chgrp = f"chgrp {group}"
    while True:
        root, name, perms = queue.get()
        if name == ".":
            path = root
        else:
            path = f"{root}/{name}"

        if root is None:
            break

        buffer.setdefault(perms, set()).add(path)

        buffered = buffer[perms]
        if len(buffered) >= blocksize:
            joined_paths = ' '.join([f"'{b}'" for b in buffered])
            if group is not None:
                os.system(f"{chgrp} " + joined_paths)
            if nontrivial:
                os.system(f"{chmod} {perms} " + joined_paths)
            buffer[perms].clear()
    for perms, buffered in buffer.items():
        if not buffered:
            continue
        joined_paths = ' '.join([f"'{b}'" for b in buffered])
        if group is not None:
            os.system(f"{chgrp} " + joined_paths)
        if nontrivial:
            os.system(f"{chmod} {perms} " + joined_paths)


def print_usage():
    """Displays basic usage information."""
    print("Usage:")
    print("  fastmod --help")
    print("  fastmod [options] perms path[s ...]")
    print("  fastmod [options] file_perms:folder_perms path[s ...]")
    print(f"  fastmod [options] [preset=\"--{DEFAULT_PRESET}\"] path[s ...]")
    print("Available options: -G<group>, -C<cores>, -B<blocksize>, -q")
    print("Use 'fastmod --help' for more information.")


def print_full_help():
    """Displays full help information."""
    print("fastmod: Multithreaded utility for recursively changing "
          "permissions.")
    print(f"v{__version__} {__copyright__}")
    print()
    print_usage()
    print()
    print("Arguments:")
    print("  PATH is the path to change permissions of. If a directory, "
          "permissions are recursively changed.")
    print("    Specify multiple paths by separating them with spaces.")
    print("  PERMS is a chmod-style permission string, eg u+rx,g=rs,o+r-w,+t")
    print("  You can  also specify separate perms for files and directories with:")
    print("    file-perms:folder-perms     e.g. u+xs,g+x,o-w:g+s,o-w")
    print("  PRESET can be *one* of the presets below:")
    max_width = max(len(preset_name) for preset_name in PRESETS)
    fil_perms_width = max(len("File Permissions"),
                          max(len(perms["fil"]) for perms in PRESETS.values()))
    dir_perms_width = max(len("Folder Permissions"),
                          max(len(perms["dir"]) for perms in PRESETS.values()))
    print(f"    {'Preset Flag'.ljust(max_width+2)}    "
          f"{'File Permissions'.ljust(fil_perms_width)}    "
          f"{'Folder Permissions'.ljust(dir_perms_width)}")
    print(f"    {'-'*(max_width+2)}    {'-'*fil_perms_width}    "
          f"{'-'*dir_perms_width}")
    for preset_name, perms in PRESETS.items():
        print(f"    --{preset_name.ljust(max_width)}    "
              f"{perms['fil'].ljust(fil_perms_width)}    "
              f"{perms['dir'].ljust(dir_perms_width)}")
    print(f"  By default, the preset is {DEFAULT_PRESET}.")
    print(
        f"  The --umask preset will apply your current umask but does not add "
        "execute permissions to files.")
    print()
    print("Options:")
    print("  Specify -G<group> to set group ownership, e.g. -Gusers.")
    print(f"  Specify -G to set group ownership to the user's primary group. "
          f"(Yours is: {PRIMARY_GROUP})")
    print("     Omit -G to keep group ownership as it is.")
    print("  If you specify group ownership with -G, this will take effect "
          "*before* permissions are applied.")
    print("  Specify -q to suppress most messages.")
    print(f"  Specify -C<cores> to set the number of worker processes to use. "
          f"Else, defaults to number available minus 1. ({DEFAULT_CORES})")
    print(f"  Specify -B<blocksize> to set the number of files changed per "
          f"batch. Else, defaults to {DEFAULT_BLOCKSIZE}.")
    print()
    print("Configuration:")
    print("  You can override defaults with these environment variables:")
    print("    FASTMOD_BLOCKSIZE, FASTMOD_CORES, FASTMOD_PRESET")
    print()
    print("Examples:")
    print("  fastmod .                            to apply default preset to cwd")
    print("  fastmod --readonly -G .              to set cwd to read-only perms and "
          "set group ownership to your primary")
    print("                                       group")
    print("  fastmod --group-allowed -Gusers .    to set cwd to user/group "
          "read/write, others read-only")
    print("                                       and set group ownership to 'users'")
    print("  fastmod a+x -G foo bar               to give everyone execute "
          "permissions to 'foo' and 'bar' and set group ")
    print("                                       ownership to your primary group")


class Config:
    """Effective configuration for this run.
    
    Pre-populated with defaults where applicable.
    """
    def __init__(self):
        self.paths = []
        self.perms_fil = PRESETS[DEFAULT_PRESET]["fil"]
        self.perms_dir = PRESETS[DEFAULT_PRESET]["dir"]
        self.group = None
        self.set_group = False
        self.ncpus = DEFAULT_CORES
        self.blocksize = DEFAULT_BLOCKSIZE
        self.quiet = False
        self.nontrivial = True


def check_perm(s):
    """Checks the permissions string to ensure it makes sense.
    
    Note that strings like '+' and 'u-' are accepted by chmod, but they do not
    actually change anything. As a convenience, we can check for these cases
    and avoid calling chmod entirely.

    Return: tuple:
        [0] Whether the string is a valid permission string;
        [1] Whether the permission string has any effect.
    """
    try:
        n = int(s)
        valid = n >= 0 and n <= 0o7777
        return valid, valid
    except ValueError:
        pass
    selectors = ["u", "g", "o", "a", ""]
    operators = ["+", "-", "="]
    permissions = ["r", "w", "x", "X", "s", "t", ""]
    nontrivial = False
    for group in s.split(","):
        sel = ""
        op = None
        for c in group:
            if c in operators:
                op = c
                if op == "=":
                    nontrivial = True
            elif not op:
                if c in selectors:
                    sel += c
                else:
                    return False, False
            elif c in permissions:
                nontrivial = True
            else:
                return False, False
        if not op:
            return False, False

    return True, nontrivial


def _test_check_perm():
    """Tests parsing logic for validating permissions strings."""
    assert check_perm("u+r,g-wx,u-r") == (True, True)
    assert check_perm("777") == (True, True)
    assert check_perm("u=r") == (True, True)
    assert check_perm("u+rX,g-w,g+s,+t") == (True, True)
    assert check_perm("ug+rwX,o+rX-w,g+s,+t") == (True, True)
    assert check_perm("+rwx") == (True, True)
    assert check_perm("u+-w") == (True, True)
    assert check_perm("u+w-") == (True, True)
    assert check_perm("=") == (True, True)
    assert check_perm("+=") == (True, True)

    assert check_perm("-") == (True, False)
    assert check_perm("+") == (True, False)
    assert check_perm("u+") == (True, False)
    assert check_perm("ug-") == (True, False)

    assert check_perm("") == (False, False)
    assert check_perm("a") == (False, False)
    assert check_perm("rwx") == (False, False)
    assert check_perm("-5") == (False, False)
    assert check_perm("999999999999") == (False, False)
    assert check_perm("u.g=rw/o+x") == (False, False)
    assert check_perm("f+oo") == (False, False)
    assert check_perm("f+oo,b-ar,+qux") == (False, False)
    assert check_perm("u+rwx,b-ar") == (False, False)
    assert check_perm("u+rwx, g+rx-w") == (False, False)


_test_check_perm()


def parse_args(argv):
    """Returns Config object of parsed arguments."""
    config = Config()
    reading_paths = False
    have_preset = False

    for arg in argv[1:]:
        if arg.startswith("-G"):
            config.set_group = True
            if arg == "-G":
                config.group = PRIMARY_GROUP
            else:
                config.group = arg[2:]
            continue
        elif arg.startswith("-C"):
            config.ncpus = int(arg[2:])
            continue
        elif arg.startswith("-B"):
            config.blocksize = int(arg[2:])
            continue
        elif arg == "-q":
            config.quiet = True
            continue
        elif arg.startswith("--"):
            preset_name = arg[2:]
            if preset_name not in PRESETS:
                print(f"fastmod: preset '{preset_name}' does not exist")
                return None
            config.perms_fil = PRESETS[preset_name]["fil"]
            config.perms_dir = PRESETS[preset_name]["dir"]
            have_preset = True
            continue
        elif ":" in arg:
            if have_preset:
                print("fastmod: cannot specify both preset and permission flags")
                return None
            try:
                config.perms_fil, config.perms_dir = arg.split(":")
                valid, nontrivial_fil = check_perm(config.perms_fil)
                if not valid:
                    print(f"fastmod: invalid permission string '{config.perms_fil}'")
                    return None
                valid, nontrivial_dir = check_perm(config.perms_dir)
                if not valid:
                    print(f"fastmod: invalid permission string '{config.perms_dir}'")
                    return None
                config.nontrivial = nontrivial_fil or nontrivial_dir
            except ValueError:
                print("fastmod: specify multiple permission flags like"
                      " 'file-perms|folder-perms'")
                print("e.g. 'u+xs,g+x,o-w:g+s,o-w'")
                return None
            continue
        else:
            if os.path.exists(arg):
                if check_perm(arg)[0]:
                    print(
                        f"fastmod: notice: '{arg}' is both a valid permission"
                        " string and a valid file path. It will be treated as"
                        " a file path. To force it to be parsed as a"
                        " permission string, prepend it with '%' as many times"
                        " as it takes to be an invalid file path.")
                reading_paths = True
            elif not reading_paths:
                while arg.startswith("%"):
                    arg = arg[1:]
                valid, nontrivial = check_perm(arg)
                if valid and have_preset:
                    print("fastmod: cannot specify both preset and permission flags")
                    return None
                if valid:
                    config.perms_fil = arg
                    config.perms_dir = arg
                    config.nontrivial = nontrivial
                    reading_paths = True
                    continue
                else:
                    if have_preset:
                        print(f"fastmod: no such path as '{arg}'")
                    else:
                        print(
                            f"fastmod: first non-flag argument '{arg}' is neither a"
                            " valid permission string nor a valid path")
                    return None
            if reading_paths:
                if not os.path.exists(arg):
                    print(f"fastmod: no such path as '{arg}'")
                    return None
                config.paths.append(arg)
                continue

    if not config.paths:
        print("fastmod: must specify at least one path")
        return None

    return config


def _test_parse_args():
    config = parse_args(["fastmod.exe", "."])
    assert config.paths == ["."]
    assert config.perms_fil == PRESETS[DEFAULT_PRESET]["fil"]
    assert config.perms_dir == PRESETS[DEFAULT_PRESET]["dir"]
    assert config.quiet == False
    assert config.set_group == False

    config = parse_args(["fastmod.exe", "u+w", "."])
    assert config.paths == ["."]
    assert config.perms_fil == "u+w"
    assert config.perms_dir == "u+w"
    assert config.quiet == False
    assert config.set_group == False

    config = parse_args(["fastmod.exe", "%%%%u+w", "."])
    assert config.paths == ["."]
    assert config.perms_fil == "u+w"
    assert config.perms_dir == "u+w"
    assert config.quiet == False
    assert config.set_group == False

    config = parse_args(["fastmod.exe", "u+rwx:u+r,+t", "."])
    assert config.paths == ["."]
    assert config.perms_fil == "u+rwx"
    assert config.perms_dir == "u+r,+t"
    assert config.quiet == False
    assert config.set_group == False

    config = parse_args(["fastmod.exe", "--readonly", "."])
    assert config.paths == ["."]
    assert config.perms_fil == PRESETS["readonly"]["fil"]
    assert config.perms_dir == PRESETS["readonly"]["dir"]
    assert config.quiet == False
    assert config.set_group == False

    config = parse_args(
        ["fastmod.exe", "u+rwx:u+r,+t", ".", "..", "../././../."])
    assert config.paths == [".", "..", "../././../."]
    assert config.perms_fil == "u+rwx"
    assert config.perms_dir == "u+r,+t"
    assert config.quiet == False
    assert config.set_group == False

    config = parse_args([
        "fastmod.exe", "-q", "-Gfoobar", "u+rwx:u+r,+t", ".", "..",
        "../././../."
    ])
    assert config.paths == [".", "..", "../././../."]
    assert config.perms_fil == "u+rwx"
    assert config.perms_dir == "u+r,+t"
    assert config.quiet == True
    assert config.set_group == True
    assert config.group == "foobar"


_test_parse_args()


def print_config(config):
    """Prints the configured changes to be made."""
    if not config.nontrivial:
        if config.set_group:
            if not config.quiet:
                print(
                    "fastmod: notice: you specified an effectively empty permission "
                    "string. Only group ownership will be changed.")
        else:
            if not config.quiet:
                print(
                    "fastmod: notice: you specified an effectively empty permission "
                    "string and did not specify to change a group. There are no "
                    "changes to perform.")
            return 0
    if not config.quiet:
        if config.nontrivial:
            if config.perms_fil:
                fil_changes = f'files({config.perms_fil})'
            if config.perms_dir:
                dir_changes = f'folders({config.perms_dir})'
        else:
            fil_changes = dir_changes = ""
        if config.set_group:
            grp_changes = f'group({config.group})'
        else:
            grp_changes = ""
        changes = [
            chg for chg in [fil_changes, dir_changes, grp_changes] if chg
        ]
        print(f"changes to make:  {'  '.join(changes)}")


def fastmod(config):
    """Runs fastmod recursively on all specified paths."""
    group_or_none = config.group if config.set_group else None
    queue = mp.Queue()
    workers = [
        mp.Process(target=worker_main,
                   args=(queue, group_or_none, config.quiet, config.blocksize,
                         config.nontrivial)) for _ in range(config.ncpus)
    ]
    for worker in workers:
        worker.start()

    dot = "."
    total = 0
    start = time.time()
    for path in config.paths:
        if os.path.isfile(path):
            queue.put_nowait((dot, path, config.perms_fil))
        else:
            total += 1
            for root, _, files in os.walk(path):
                queue.put_nowait((root, dot, config.perms_dir))
                for file in files:
                    queue.put_nowait((root, file, config.perms_fil))
                    total += 1

    for _ in workers:
        queue.put_nowait((None, None, None))

    for worker in workers:
        worker.join()

    duration = time.time() - start

    s_per_file = f"{duration / total:.05f}" if total != 0 else "NA"
    fs = "s" if total != 1 else ""
    print(f"set permissions on {total} file{fs} in {duration:.03f} seconds "
          f"({s_per_file} s/file; {total/duration:.01f} files/s)")


def main(argv):
    """Entry point for the application."""
    if not argv[1:]:
        print_usage()
        return 1

    if argv[1] in ("-h", "--help"):
        print_full_help()
        return 1

    config = parse_args(argv)
    if config is None:
        return 1
    print_config(config)

    fastmod(config)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    raise ImportError("fastmod is run as a script, not included as a module.")
