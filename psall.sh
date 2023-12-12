#!/bin/bash

# Prints process information in a very compact format, truncating lines to the terminal's width.
# ps prints etime in the format "days-hours:minutes:seconds" when a process has been running for
# more than a day. But this takes up more space than just showing "hours:minutes:seconds" so this
# script converts to that format. (There's no way to specify this in ps itself)
# Also this uses the minimal padding between columns needed

# Converts spaces in columns to Record Separator character (0x1E)
# This way we can preserve leading spaces in the final column, the argv, so the process tree
# displays correctly.
SED_COLS_TO_RS_STRING='s/(\S+)[ ]+(\S+)[ ]+(\S+)[ ]+(\S+)[ ]+(\S+) (.*)/\1\x1e\2\x1e\3\x1e\4\x1e\5\x1e\6/g'

PS_OUTPUT=$(ps f -o pid,user,pcpu,state,etime,args -N --ppid 2)
PS_OUTPUT=$(sed -r "$SED_COLS_TO_RS_STRING" <<< "$PS_OUTPUT")

awk -F"$(echo -e '\x1e')" '

# Spool up output rows so they can be printed with proper width at the end
{
    # The whole command string is treated as one column even though it
    # could contain spaces
    argv = $6
    #for (i = 7; i <= NF; i++) {
    #    argv = argv " " $i
    #}

    pids[NR] = $1
    users[NR] = $2
    pcpus[NR] = $3
    states[NR] = $4
    etimes[NR] = $5
    argvs[NR] = argv
}


NR==1 { 
    $3 = "CPU"  # replace "%CPU" with just "CPU"

    pcpus[1] = "CPU"

    maxlen_pid = length($1)
    maxlen_user = length($2)
    maxlen_pcpu = length($3)
    maxlen_state = length($4)
    maxlen_etime = length($5)
}


NR>1 {
    
    # Make etime more compact by converting days-hours:minutes:seconds
    # to just hours:minutes:seconds
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
            etimes[NR] = etime
        }
    }

    # Update column widths
    if (length($1) > maxlen_pid) { maxlen_pid = length($1) }
    if (length($2) > maxlen_user) { maxlen_user = length($2) }
    if (length($3) > maxlen_pcpu) { maxlen_pcpu = length($3) }
    if (length($4) > maxlen_state) { maxlen_state = length($4) }
    if (length(etime) > maxlen_etime) { maxlen_etime = length(etime) }
}

END {
    # Print all rows with correct widths
    fmt = "%"maxlen_pid"s %-"maxlen_user"s %"maxlen_pcpu"s %-"maxlen_state"s %"maxlen_etime"s %s\n"

    for (i = 1; i <= NR; i++) {
        printf fmt, pids[i], users[i], pcpus[i], states[i], etimes[i], argvs[i]
    }
}
' <<< "$PS_OUTPUT" | awk "BEGIN { cols=$(tput cols) }   { print substr(\$0, 1, cols) }"
