# Just some nice defaults I've built up for a typical Linux setup.
# Especially nice in networked filesystems shared by multiple groups,
# but just as useful on a serious home setup.


set -o noclobber  # Don't redirect output to files that already exist, effectively overwriting them

shopt -s globstar  # Allow fancy globbing syntax like '**' to match any number of directory levels
shopt -u progcomp  # Don't escape '$' when tab completing (so annoying, why would this ever be the default!?)

ulimit -c 0  # no core dumps please



alias ls="ls --color=auto"
alias grep="grep --color=auto"


# Uncomment the below to set your primary group even if you don't have the
# ability to do so via usermod. Set EFFECTIVE_PRIMARY_GROUP to your desired
# primary group, and it will be set whenever this script is sourced.
#if [ "$PS1" ]; then
#    EFFECTIVE_PRIMARY_GROUP=MyDesiredPrimaryGroup
#    __oldprimarygrp=`id -gn`
#    if [[ $__oldprimarygrp != $EFFECTIVE_PRIMARY_GROUP ]]; then
#        newgrp $EFFECTIVE_PRIMARY_GROUP
#    fi
#fi

umask u=rwx,g=rx,o=

export EDITOR=vim
export PAGER=less
export XDG_RUNTIME_DIR=/tmp/run/user/`id -u`

alias gt=gnome-terminal
alias gterm=gnome-terminal
alias vg=gvim
alias h=history
alias ll="ls -lah"
alias dusha="du -sh --apparent-size"
alias pstree="ps -e -o pid,user,state,rss,pcpu,etime,args --forest"
alias 1="cd ../."
alias 2="cd ../../."
alias 3="cd ../../../."
alias 4="cd ../../../../."
alias x="exit"
alias rp="readlink -f"
alias portusage="lsof -i -P -n"


# Requires 'pbzip2' on PATH: https://github.com/ruanhuabin/pbzip2
function tar_and_remove {
    tar -cf $1.tar.bz2 -Ipbzip2 $1 --remove-files
}

function replace_all {
    if [[ -z "$1" || -z "$2" || -z "$3" ]]; then
        echo "replace_all <path> <search-string> <replace-string>"
        return
    fi
    find "$1" -type f -exec sed -i -e "s/$2/$3/g" {} \;
}

function vimwich {
    vim `which "$1"`
}

# The function that everyone should have in their bashrc.
# Solves the common problem of:
#   $ ls
#   $ ls foo
#   $ ls foo/bar
#   $ ls foo/bar/baz
#   $ vim foo/bar/baz/qux  # <--- have to jump to the beginning of the command and replace 'ls' with 'vim'
# Instead, you can now do:
#   $ xp
#   $ xp foo
#   $ xp foo/bar/baz
#   $ xp foo/bar/baz/qux   # <--- when arg is a file, opens in $EDITOR
#   $ xp foo/bar/baz/qux -xa rm %    # <--- 'xp <file|folder> -xa <command [args ...]>' 
#                                         will run <command> with <args>, using '%' as a substitution
#                                         for the file name. (-xa is for xargs)
#   $ xp foo/bar/baz/exe -x 123 456  # <--- runs 'foo/bar/baz/exe' with args '123', '456'
# The nice thing this adds is being able to change the behavior by appending, rather than prepending,
# to the previous command.
function explore {
    if [ -z "$1" ]; then
        fn="${FUNCNAME[0]}"
        echo "$fn: the file utility you always wanted, but never knew you needed"
        echo "usage:"
        echo "  $fn <folder>                         to list contents of folder"
        echo "  $fn <file>                           to open file in your \$EDITOR"
        echo "  $fn <folder> -cd                     to cd to folder"
        echo "  $fn <file> -x  [args ...]            to execute <file>, optionally with args"
        echo "  $fn <file> -xa <cmd> [args ...]      to run <cmd> on the given file, using '%' as a placeholder."
        echo "  $fn <folder> -xaf  <cmd> [args ...]  to run <cmd> on all top-level files in <folder>, using '%' as a placeholder."
        echo "  $fn <folder> -xarf <cmd> [args ...]  to run <cmd> on all contents of <folder>, recursively, using '%' as a placeholder."
        return
    fi

    if [[ -d "$1" && "$2" == "-cd" ]]; then
        cd "$1"
    elif [[ "$2" == "-xaf" ]]; then
        find "$1" -maxdepth 1 -mindepth 1 -print0 | xargs -0 -I% "${@:3}"
    elif [[ "$2" == "-xafr" ]]; then
        find "$1" -mindepth 1 -print0 | xargs -0 -I% "${@:3}"
    elif [[ "$2" == "-xa" ]]; then
        echo "$1" | xargs -0 -I% "${@:3}"
    elif [ -d "$1" ]; then
        ll "$1"
    elif [[ -x "$1" && "$2" == "-x" ]]; then
        $1 ${@:3}
    else
        "$EDITOR" "$1"
    fi
}
alias xp=explore

function mkcd {
    mkdir -p "$1" && cd "$1"
}

function cdls {
    cd "$1" && ls
}

function pyinit {
    mkdir -p "$1"
    touch "$1"/__init__.py
}

export PATH="/home/$USER/.local/bin:/home/$USER/bin:/usr/local/bin:/usr/bin:/usr/sbin:/bin:/sbin"

RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[94m'
CYAN='\033[36m'
GREY='\033[38;5;244m'
RESET='\033[0m'
BLINK='\033[5m'
BOLD='\033[1m'
ORANGE='\033[38;5;208m'
DARK_ORANGE='\033[38;5;202m'
GOLD='\033[38;5;214m'
PURPLE='\033[38;5;128m'

SUNSET1='\033[38;5;161m'
SUNSET2='\033[38;5;162m'
SUNSET3='\033[38;5;163m'
SUNSET4='\033[38;5;164m'
SUNSET5='\033[38;5;165m'

REDHLGHT='\033[41m\033[37m'


function cwdtags {
    tags=""

    # Indicate when in a read-only directory
    if [ ! -w . ]; then
        tags="$tags \033[31m[not writable]\033[0m"
    fi

    # Indicate when in a different group's area
    owning_group="$(ls -la | head -n2 | tail -n1 | awk {'print$4'})"
    if [[ "$(groups)" != *"$owning_group"* ]]; then
        tags="$tags \033[36m[external group: $owning_group]\033[0m"
    fi

    # Much more lightweight way to show git branch than that
    # obnoxiously slow git-prompt thing
    branch="$(git branch --show-current 2>/dev/null)"
    if [[ $? == 0 ]]; then
        tags="$tags \033[94m[$branch]\033[0m"
    fi
    
    echo -e "$tags"
}

function update_tty_title {
    echo -ne "\033]0;$(whoami)@$(hostname)\007"
}

if [ "$PS1" ]; then
    whoami=`whoami`
    color_whoami="$YELLOW$whoami$RESET@"
    if [[ "$whoami" != "$PRIMARY_USER" ]]; then
        color_whoami="$RED$whoami$RESET@"
    fi

    if [ -e "$SSH_TTY" ]; then
        PS1="\$(update_tty_title)\n[\u@\h] \w\n% "
    else
        if [[ "$whoami" == "root" ]]; then
            dir_color="$RED$BOLD"
            perc="$RED$BOLD#"
        else
            dir_color="$GOLD"
            perc="%"
        fi
        
        # PS1="\n$RESET$color_whoami$YELLOW\h $RESET[$dir_color\$(~/public/libexec/cwdabbr --abbreviate)$RESET]\$(cwdtags)\n$perc_color% $RESET"

        PS1="$RESET[$color_whoami$YELLOW\h$RESET $dir_color\$(~/public/libexec/cwdabbr --abbreviate)$RESET]$perc $RESET"
    fi
fi

