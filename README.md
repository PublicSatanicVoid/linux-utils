## linux-utils

Some Linux utilities that I think should be standard for anyone working in a multi-user and/or multi-project environment.

Developed over the course of my study at University of Minnesota (CSE Labs system); my research using the Minnesota Supercomputing Institute; and my employment at Broadcom Corp.


### Brief synopsis of tools

**fastmod** - a Python tool for quickly changing permissions on large folders. More effective with more CPU cores (up to the point that the drive being modified is saturated with I/O; for good drives this is at *least* 16 threads). Also allows setting separate permissions on files and folders. (Yes, you can use +X to only target folders, but what about g+s or +t?) Also has handy presets. And also supports changing group ownership.

**jumpto** - a Python tool + Bash wrapper for storing folder locations by project / label. Makes it easier to navigate large filesystems without having to set tons of environment variables. Can call the Python script directly, or for a more streamlined experience use the wrapper script and set up an alias to it: `alias j='source /path/to/jumpto_wrapper.sh'`

**starter.bashrc** - a nice set of defaults for your `.bashrc`.
