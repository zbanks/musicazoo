#include <string.h>

#include "musicazoo.h"

static bool youtube_match(const char * input, mz_cmd cmd) {
    const char * NAME = "youtube";
    if (strncasecmp(input, NAME, strlen(NAME)) != 0) return false;
    input += strlen(NAME);

    if (*input++ != ' ') return false;

    while (*input == ' ') input++;
    strncpy(cmd, input, sizeof(mz_cmd));
    return true;
}

static coroutine void youtube(int cmd_ch, int desc_ch) {
    int time = 0;

    mz_cmd arg;
    int rc = chrecv(cmd_ch, arg, sizeof(mz_cmd), -1);
    if (rc != 0) return;

    printf("youtube: playing '%s'\n", arg);

    while (1) {
        mz_cmd desc;
        snprintf(desc, sizeof desc, "youtube [%d:%02d] '%s'",
                time / 60, time % 60, arg);

        rc = chsend(desc_ch, desc, sizeof(mz_cmd), -1);
        if (rc != 0 && errno != ETIMEDOUT) return;

        time++;
        if (time > 120) break;

        mz_cmd cmd;
        rc = chrecv(cmd_ch, cmd, sizeof(mz_cmd), now() + 100);
        if (rc != 0 && errno != ETIMEDOUT) return;
        if (rc != 0) continue;

        printf("youtube got cmd '%s'\n", cmd);
    }

    printf("youtube '%s' terminating\n", arg);
}

struct mz_module mz_youtube = {
    .name = "YouTube",
    .match_fn = &youtube_match,
    .run_coro = &youtube,
};
