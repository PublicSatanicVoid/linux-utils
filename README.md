# linux-utils

Some Linux utilities that I think should be standard for anyone working in a multi-user and/or multi-project environment.

Developed over the course of my study at University of Minnesota (CSE Labs system); my research using the Minnesota Supercomputing Institute; and my employment at Broadcom Corp.


## Setup

1. (Optional) Clone the `pbzip2` repository [here](https://github.com/ruanhuabin/pbzip2) - this lets you quickly compress files to `.bz2` and is required for the `tar_and_remove` helper function in `starter.bashrc`.
2. Ensure you have [Python 3.11](https://www.python.org/downloads/release/python-3113/) at `/usr/local/bin/python3.11`; otherwise, edit the Python scripts to point to your own recent Python interpreter.
3. If you don't already have it, make a `bin` directory in your home folder.
4. Copy the scripts you want from this repository to that `bin` directory.
5. (Optional) Remove the `.py` extensions from scripts you intend to call directly, or set up aliases to them.
6. Add desired sections of `starter.bashrc` to your `.bashrc`.


## Brief synopsis of tools

### fastmod

A Python tool for quickly changing permissions on large folders. More effective with more CPU cores (up to the point that the drive being modified is saturated with I/O; for good drives this is at *least* 16 threads). Also allows setting separate permissions on files and folders. (Yes, you can use +X to only target folders, but what about g+s or +t?) Also has handy presets. And also supports changing group ownership.

    % fastmod g+w /big/folder
    % fastmod :g+s /big/folder2
    % fastmod --umask /big/folder3
    % fastmod -Gothergroup --umask /big/folder4


### jumpto

A Python tool + Bash wrapper for storing folder locations by project / label. Makes it easier to navigate large filesystems without having to set tons of environment variables. Can call the Python script directly, or for a more streamlined experience use the wrapper script and set up an alias to it: `alias j='source /path/to/jumpto_wrapper.sh'`


### abbreviate_cwd

Build with: `gcc -o cwdabbr -O3 -march=native abbreviate_cwd.c`

Abbreviates your current working directory using a predefined list of shortcuts, which can be exported into the shell of your choice. Use this to shorten the directory name in your prompt string. Also shortens home directories using the `~` notation. Bash example:

_assumes you compiled `abbreviate_cwd.c` to `~/libexec/cwdabbr`_

_`~/etc/folder_shortcuts.csv`:_

    workspace,/network/locations/always/get/so/long/here/is/my/workspace/area
    testcases,/another/network/location/oh/boy

_`~/.bashrc`:_

    export CWD_SHORTCUTS_FILE="$(readlink -f ~/etc/folder_shortcuts.csv)"
    eval "$(~/libexec/cwdabbr --export bash)"

    PS1="\u@\h [\$(~/libexec/cwdabbr --abbreviate)]\n% "

_`Example`:_

    % source ~/.bashrc

    user@host [/some/location]
    % cd /regular/location

    user@host [/regular/location]
    % cd ~/etc

    user@host [~/etc]
    % cd /another/network/location/oh/boy

    user@host [$testcases]
    % cd /another/network/location/oh/boy/whats/next

    user@host [$testcases/whats/next]
    %  echo "$testcases"
    /another/network/location/oh/boy

### starter.bashrc

A nice set of defaults for your `.bashrc`.
