#!/bin/bash

if [ "${BASH_SOURCE[0]}" == "$0" ]; then
    echo "jumpto.sh: this script is meant to be sourced."
    exit 1
else
    script_dir="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
    dest_holder="$(readlink -f ~)/.jumpto.tmp"
    _JUMPTO="$dest_holder" $script_dir/jumpto.py "$@"
    if [ -f "$dest_holder" ]; then
        dest="$(< "$dest_holder")"
        cd "$dest"
        rm "$dest_holder"
    fi
fi
