/* Utility to abbreviate cwd with configured list of shortcuts.
    If abbreviated cwd is still too long, skip intermediate directory
    levels; and if it's *still* too long, show relative path instead.

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

#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

#include <wchar.h>
#include <locale.h>

// Truncates paths to this many levels at the front and back
// e.g. with max front of 2 and max back of 1,
//          /a/b/c/d/e/f/g
// becomes
//          /a/b/…/g

#define MAX_FRONT_LEVELS 1
#define MAX_BACK_LEVELS 2

#define soft_shorten_after 23
#define shorten_after 30

#define SHORT_FRONT_LEVELS 0
#define SHORT_BACK_LEVELS 2

// when falling back to relative path, show up to this many levels
#define REL_SHORT_LEVELS 2


int wstrlen(wchar_t* str) {
    int i;
    for (i = 0; str[i] != 0; ++i) {}
    return i;
}


int main(int argc, char* argv[]) {
    setlocale(LC_ALL, "");
    
    if (argc == 1) {
        fprintf(stderr, "Usage: %s [--export <bash|tcsh> | --abbreviate [--short]]\n", argv[0]);
        exit(1);
    }

    const char* shortcuts_file = getenv("CWD_SHORTCUTS_FILE");
    if (!shortcuts_file) {
        fprintf(stderr, "CWD_SHORTCUTS_FILE environment variable not set\n");
        exit(1);
    }

    char cwd[PATH_MAX];
    wchar_t wcwd[PATH_MAX];  // when adding ellipsis, must use a wchar string instead
    getcwd(cwd, sizeof(cwd));

    if (!strcmp(argv[1], "--abbreviate") && getuid() == 0) {
        printf("%s", basename(cwd));
        return 0;
    }

    FILE* fp = fopen(shortcuts_file, "r");
    if (fp == NULL) {
        if (!strcmp(argv[1], "--abbreviate")) {
            printf("%s", basename(cwd));
        }
        fprintf(stderr, "Error opening file \"%s\"\n", shortcuts_file);
        return 1;
    }

    if (!strcmp(argv[1], "--abbreviate")) {
        int shorten = argc > 2 && !strcmp(argv[2], "--short");

        char cwd_copy[PATH_MAX];
        strncpy(cwd_copy, cwd, PATH_MAX);

        char* home = getenv("HOME");
        int home_len = strlen(home);

        int cwd_has_home = (strstr(cwd, home) == cwd);

        // Create abbreviate relative path, but don't include elements of $HOME
        int i;
        char* relpath = cwd_copy + strlen(cwd_copy);
        int level = 1;
        for (i = strlen(cwd_copy); i >= 0; --i) {
            if (cwd_copy[i] == '/') {
                char* testpath = cwd_copy + i + 1;
                if (level <= REL_SHORT_LEVELS && (level == 1 || strlen(testpath) < shorten_after)) {
                    relpath = testpath;
                    if (cwd_has_home && i <= 1+home_len) {
                        relpath -= 2;
                        relpath[0] = '~';
                        relpath[1] = '/';
                        break;
                    }
                    ++level;
                }
                else break;
            }
        }

        // Process configured list of abbreviations
        // Each line is 'ABBREVIATION,ABSPATH' where 'ABBREVIATION' does NOT include the '$'
        // Stops after the first match. So, line ordering in this file matters.
        char* line = malloc(1024);
        int abbreviated = 0;
        while (fgets(line, 1024, fp) != NULL) {
            char* path = strstr(line, ",") + 1;
            path[strlen(path) - 1] = '\0';
            *(path - 1) = '\0';

            char* needle = strstr(cwd, path);
            if (needle == cwd && needle != NULL && (cwd[strlen(path)] == '/' || cwd[strlen(path)] == '\0')) {
                char* suffix = malloc(1024);
                strcpy(suffix, needle + strlen(path));
                *(needle) = '$';
                strcpy(needle + 1, line);
                strcpy(needle + strlen(line) + 1, suffix);
                abbreviated = 1;
                break;
            }
        }

        if (!abbreviated) {
            // Abbreviate home directories, $HOME --> ~   and  /home/OTHER --> ~other
            if (home != NULL) {
                char* needle = strstr(cwd, home);
                if (needle == cwd && needle != NULL) {
                    char* suffix = needle + strlen(home);
                    char* result = malloc(1 + strlen(cwd) - strlen(suffix));
                    result[0] = '~';
                    strcpy(result + 1, suffix);
                    strncpy(cwd, result, PATH_MAX);
                }
            }
            char* needle = strstr(cwd, "/home/");
            if (needle == cwd && needle != NULL) {
                char* suffix = needle + strlen("/home/");
                strcpy(needle, "~");
                char* result = malloc(1 + strlen(suffix));
                result[0] = '~';
                strcpy(result + 1, suffix);
                strncpy(cwd, result, PATH_MAX);
            }
        }

        int n_levels = 0;
        int len = strlen(cwd);
        for (i = 0; i < len; ++i) {
            if (cwd[i] == '/') {
                ++n_levels;
            }
        }
        int max_front_levels = (len > shorten_after ? SHORT_FRONT_LEVELS : MAX_FRONT_LEVELS);
        int max_back_levels = (len > shorten_after ? SHORT_BACK_LEVELS : MAX_BACK_LEVELS);
        
        // Remove intermediate directory names if there are too many
        if (n_levels > max_front_levels + max_back_levels + 1) {
            int front_slash = 0;
            int back_slash = 0;
            int starting_end_pos = 0;
            
            int abbr_len = 2;  // 1 for '…' and 1 for null terminator
            

            // Count number of front and back levels to include
            for (i = 0; i < len; ++i) {
                ++abbr_len;
                if (cwd[i] == '/') {
                    ++front_slash;
                    if (front_slash > max_front_levels) {
                        break;
                    }
                }
            }
            for (i = len - 1; i >= 0; --i) {
                ++abbr_len;
                if (cwd[i] == '/') {
                    ++back_slash;
                    if (back_slash >= max_back_levels) {
                        starting_end_pos = i;
                        break;
                    }
                }
            }

            // Add 'front_slash' many front levels
            wchar_t abbr_cwd[abbr_len];
            front_slash = 0;
            back_slash = 0;
            int out_pos = 0;
            for (; out_pos < len; ++out_pos) {
                abbr_cwd[out_pos] = cwd[out_pos];
                if (cwd[out_pos] == '/') {
                    ++front_slash;
                    if (front_slash > max_front_levels) {
                        break;
                    }
                }
            }

            abbr_cwd[++out_pos] = 0x2026; // unicode ellipsis
            ++out_pos;
            
            // Add 'back_slash' many back levels
            for (i = starting_end_pos; i < len; ++i, ++out_pos) {
                abbr_cwd[out_pos] = cwd[i];
            }
            abbr_cwd[out_pos] = '\0';

            // Now that we know the shortened relative path AND the abbreviated-with-ellipsis path,
            // determine which one to use            
            if (
                (shorten || wstrlen(abbr_cwd) > shorten_after)  // whether we have to shorten the path
                && wstrlen(abbr_cwd) > soft_shorten_after  // whether the abbreviated path is too long
                && strlen(relpath) < wstrlen(abbr_cwd)  // whether the relative path is shorter
            )
            {
                printf("%s", relpath);
            }
            else {
                wprintf(L"%ls", abbr_cwd);
            }
        }
        else {
            if (shorten && strlen(cwd) > soft_shorten_after && strlen(relpath) < strlen(cwd)) {
                printf("%s", relpath);
            }
            else {
                printf("%s", cwd);
            }
        }
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
