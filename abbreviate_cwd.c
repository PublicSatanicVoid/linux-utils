/* Utility to abbreviate cwd with configured list of shortcuts.

    Shortcuts are read from the file specified in the environment
    variable
        CWD_SHORTCUTS_FILE
    which must be in CSV format
        <shortcut>,</path/to/file>\n
        ...

    Run with '--abbreviate' to get the abbreviated cwd.
    Run with '--export <bash|tcsh>' to get bash export or tcsh setenv
        commands to set  the environment variables corresponding to the
        shortcuts.

    Copyright (c) 2023 Broadcom Corporation. All rights reserved.
    Public Domain. See accompanying LICENSE file for full terms.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

int main(int argc, char* argv[]) {
    if (argc == 1) {
        fprintf(stderr, "Usage: %s [--export <bash|tcsh> | --abbreviate]\n", argv[0]);
        exit(1);
    }

    const char* shortcuts_file = getenv("CWD_SHORTCUTS_FILE");
    if (!shortcuts_file) {
        fprintf(stderr, "CWD_SHORTCUTS_FILE environment variable not set\n");
        exit(1);
    }

    char cwd[PATH_MAX];
    getcwd(cwd, sizeof(cwd));

    FILE* fp = fopen(shortcuts_file, "r");
    if (fp == NULL) {
        if (!strcmp(argv[1], "--abbreviate")) {
            printf("%s", cwd);
        }
        fprintf(stderr, "Error opening file \"%s\"\n", shortcuts_file);
        return 1;
    }

    if (!strcmp(argv[1], "--abbreviate")) {
        // Process configured list of abbreviations
        char line[1024];
        int abbreviated = 0;
        while (fgets(line, 1024, fp)!= NULL) {
            char* path = strstr(line, ",") + 1;
            path[strlen(path) - 1] = '\0';
            *(path - 1) = '\0';

            char* needle = strstr(cwd, path);
            if (needle == cwd && needle != NULL) {
                char* suffix = needle + strlen(path);
                *(needle) = '$';
                strcpy(needle + 1, line);
                strcpy(needle + strlen(line) + 1, suffix);
                abbreviated = 1;
                break;
            }
        }
        
        if (!abbreviated) {
            // Abbreviate home directories, $HOME --> ~   and  /home/OTHER --> ~other
            char* home = getenv("HOME");
            if (home != NULL) {
                char* needle = strstr(cwd, home);
                if (needle == cwd && needle != NULL) {
                    char* suffix = needle + strlen(home);
                    strcpy(needle, "~");
                    strcpy(needle + strlen("~"), suffix);
                }
            }
            char* needle = strstr(cwd, "/home/");
            if (needle == cwd && needle != NULL) {
                char* suffix = needle + strlen("/home/");
                strcpy(needle, "~");
                strcpy(needle + strlen("~"), suffix);
            }
        }

        printf("%s", cwd);
    }

    else if (!strcmp(argv[1], "--export")) {
        if (argc == 2) {
            fprintf(stderr, "Usage: %s --export <bash|tcsh>\n", argv[0]);
        }
        int bash_mode = !strcmp(argv[2], "bash");
        char line[1024];
        while (fgets(line, 1024, fp) != NULL) {
            char* path = strstr(line, ",") + 1;
            path[strlen(path) - 1] = '\0';
            *(path - 1) = '\0';

            if (bash_mode) {
                printf("export %s=\"%s\"\n", line, path);
            }
            else {
                printf("setenv %s \"%s\"\n", line, path);
            }
        }
    }

    fclose(fp);
    return 0;
}
