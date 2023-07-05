To make 'jumpto' as convenient as possible, alias 'jumpto' (or even better, 'j') in your bashrc/cshrc/etc to:
    'source /path/to/jumpto_wrapper.sh'

This allows the script to change your current working directory without creating a subshell.
Creating subshells every time you want to jump somewhere is a little wasteful, and not very convenient (you lose your history, for example) so while either method will work, setting up an alias to source the wrapper script is the better way.
