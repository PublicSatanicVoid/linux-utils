# Source this file to make your terminal prompt come from the background process.
# Reduces latency compared to assembling the prompt on-demand (including calling
# subprocesses)

# TODO update this line with your installation path of fastprompt
_FASTPROMPT_BASE="${HOME}/libexec"
_FASTPROMPT_TMP="${XDG_RUNTIME_DIR:-/tmp}"

# Pidfiles and pipes: per-process
_FASTPROMPT_FIFO="${_FASTPROMPT_TMP}/fastprompt.$$.ps1.fifo"
_FASTPROMPT_FIFO_RPS1="${_FASTPROMPT_TMP}/fastprompt.$$.rps1.fifo"
_FASTPROMPT_PIDFILE="${_FASTPROMPT_TMP}/fastprompt.$$.pid"

# Kill existing server when reloading
if [ -f "$_FASTPROMPT_PIDFILE" ]; then
    kill $(< "$_FASTPROMPT_PIDFILE") 2>/dev/null
fi

# Recreate fifos when reloading
rm -f "$_FASTPROMPT_FIFO"
mkfifo "$_FASTPROMPT_FIFO"

rm -f "$_FASTPROMPT_FIFO_RPS1"
mkfifo "$_FASTPROMPT_FIFO_RPS1"

# Start the server process in the background, and wait for it to become ready.
ready=0
trap 'ready=1' SIGUSR1

nohup "${_FASTPROMPT_BASE}/prompt-server.py" "$_FASTPROMPT_FIFO" "$_FASTPROMPT_FIFO_RPS1" >/dev/null 2>&1 &!
serv_pid=$!

echo "$serv_pid" >| "$_FASTPROMPT_PIDFILE"

trap "kill $serv_pid" EXIT
while [ $ready -ne 1 ]; do
    sleep 0.1
done

# Generate the prompt via the precmd function, instead of setting PS1 statically.
precmd() {
    extra_precmd

    kill -SIGUSR1 $serv_pid
    read _prompt < "$_FASTPROMPT_FIFO"
    read _rprompt < "$_FASTPROMPT_FIFO_RPS1"
    PS1="$_prompt "
    RPS1="$_rprompt"
}
