rm -f /tmp/message
mkfifo /tmp/message

ready=0
trap 'ready=1' SIGUSR1
~/libexec/prompt-serv.py /tmp/message &
serv_pid=$!
trap "kill $serv_pid" EXIT
while [ $ready -ne 1 ]; do
    sleep 0.1
done
echo "**ready**"

PS1=''


precmd() {
    kill -SIGUSR1 $serv_pid
    read _prompt </tmp/message
    PS1="$_prompt "
}
