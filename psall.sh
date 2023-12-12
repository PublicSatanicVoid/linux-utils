#!/bin/bash

# Prints process information in a very compact format, truncating lines to the terminal's width.
# ps prints etime in the format "days-hours:minutes:seconds" when a process has been running for
# more than a day. But this takes up more space than just showing "hours:minutes:seconds" so this
# script converts to that format. (There's no way to specify this in ps itself)
# Also this uses the minimal padding between columns needed (plus one extra space for readability,
# between %cpu and etime, since they are adjacent numerical columns)

ps f -o pid,user,state,%cpu,etime,args -N --ppid 2 | awk '
NR==1 { 
    maxlen_pid = length($1)
    maxlen_user = length($2)
    maxlen_state = length($3)
    maxlen_pcpu = length($4)
    maxlen_etime = length($5)
}


{
    argv = $6
    for (i = 7; i <= NF; i++) {
        argv = argv " " $i
    }

    pids[NR] = $1
    users[NR] = $2
    states[NR] = $3
    pcpus[NR] = $4
    etimes[NR] = $5
    argvs[NR] = argv
}


NR>1 {
    etime = $5

    split(etime, days_hms, "-")
    
    if (length(days_hms) > 1) {
        days = days_hms[1] + 0
        hms = days_hms[2]

        split(hms, h_m_s, ":")

        if (length(h_m_s) == 3) {
            hours = h_m_s[1] + 0
            minutes = h_m_s[2] + 0
            seconds = h_m_s[3] + 0

            tot_hours = hours + (24 * days)

            etime = tot_hours ":" minutes ":" seconds
        }
    }

    if (length($1) > maxlen_pid) { maxlen_pid = length($1) }
    if (length($2) > maxlen_user) { maxlen_user = length($2) }
    if (length($3) > maxlen_state) { maxlen_state = length($3) }
    if (length($4) > maxlen_pcpu) { maxlen_pcpu = length($4) }
    if (length(etime) > maxlen_etime) { maxlen_etime = length(etime) }
}

END {
    fmt = "%"maxlen_pid"s %"maxlen_user"s %"maxlen_state"s %"maxlen_pcpu"s  %"maxlen_etime"s %s\n"

    for (i = 1; i <= NR; i++) {
        printf fmt, pids[i], users[i], states[i], pcpus[i], etimes[i], argvs[i]
    }
}
' | awk "BEGIN { cols=$(tput cols) }     { print substr(\$0, 1, cols) }"
