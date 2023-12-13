# Source this file to make your terminal prompt come from the background process.
# Reduces latency compared to assembling the prompt on-demand (including calling
# subprocesses)

# TODO update this line with your installation path of fastprompt
_FASTPROMPT_BASE="$HOME/projects/linux-utils/fastprompt"

_FASTPROMPT_FIFO_PATH="/tmp/fastprompt.$$.fifo"

rm -f "$_FASTPROMPT_FIFO_PATH"
mkfifo "$_FASTPROMPT_FIFO_PATH"

# Start the server process in the background, and wait for it to become ready.
ready=0
trap 'ready=1' SIGUSR1
"$_FASTPROMPT_BASE"/prompt-server.py "$_FASTPROMPT_FIFO_PATH" &
serv_pid=$!
trap "kill $serv_pid" EXIT
while [ $ready -ne 1 ]; do
    sleep 0.1
done

# Generate the prompt via the precmd function, instead of setting PS1 statically.
precmd() {
    kill -SIGUSR1 $serv_pid
    read _prompt < "$_FASTPROMPT_FIFO_PATH"
    PS1="$_prompt "
}
