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
alias 1="cd ../."
alias 2="cd ../../."
alias 3="cd ../../../."
alias 4="cd ../../../../."
alias x="exit"
alias rp="readlink -f"


function tar_and_remove {
    tar -cf $1.tar.bz2 -I/projects/libdev_py/bin/pbzip2 $1 --remove-files
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

function explore {
    if [ -z "$1" ]; then
        explore .
        return
    fi

    if [[ -d "$1" && "$2" == "cd" ]]; then
        cd "$1"
    elif [ -d "$1" ]; then
        ll "$1"
    elif [[ -x "$1" && "$2" == "x" ]]; then
        $1 ${@:3}
    else
        vim "$1"
    fi
}
alias xp=explore

function mkcd {
    mkdir -p "$1" && cd "$1"
}

function cdls {
    cd "$1" && ls
}

export PATH="/home/$USER/.local/bin:/home/$USER/bin:/usr/local/bin:/usr/bin:/usr/sbin:/bin:/sbin"

RED="\$(echo -e \e[31m)"
GREEN="\$(echo -e \e[32m)"
YELLOW="\$(echo -e \e[33m)"
BLUE="\$(echo -e \e[94m)"
CYAN="\$(echo -e \e[36m)"
RESET="\$(echo -e \e[0m)"
BLINK="\$(echo -e \e[5m)"
BOLD="\$(echo -e \e[1m)"

function cwdtags {
    tags=""

    # Indicate when in a read-only directory
    if [ ! -w . ]; then
        tags="$tags \e[31m[not writable]\e[0m"
    fi

    # Indicate when in a different group's area
    owning_group="$(ls -la | head -n2 | tail -n1 | awk {'print$4'})"
    if [[ "$(groups)" != *"$owning_group"* ]]; then
        tags="$tags \e[36m[external group: $owning_group]\e[0m"
    fi

    # Much more lightweight way to show git branch than that
    # obnoxiously slow git-prompt thing
    branch="$(git branch --show-current 2>/dev/null)"
    if [[ $? == 0 ]]; then
        tags="$tags \e[94m[$branch]\e[0m"
    fi
    
    echo -e "$tags"
}

if [ "$PS1" ]; then
    whoami=`whoami`
    color_whoami="$GREEN$whoami"
    if [[ "$whoami" == "root" ]]; then
        color_whoami="$RED$BOLD$whoami"
    fi
    PROMPT_PREFIX="\n$color_whoami$RESET@$BLUE\$(hostname --fqdn)$RESET:$YELLOW\w$RESET\$(cwdtags)"
    PROMPT_SUFFIX="$RESET\n$ "

    PS1="$PROMPT_PREFIX$PROMPT_SUFFIX"
fi
