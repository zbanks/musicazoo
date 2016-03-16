#include <string.h>

#include "musicazoo.h"

static bool youtube_match(const char * input, struct mz_buf * cmd) {
    const char * NAME = "youtube";
    if (strncasecmp(input, NAME, strlen(NAME)) != 0) return false;
    input += strlen(NAME);

    if (*input++ != ' ') return false;

    while (*input == ' ') input++;
    mz_buf_printf(cmd, "%s", input);
    return true;
}

static coroutine void youtube(int cmd_ch, int desc_ch) {
    int time = 0;

    struct mz_buf arg = MZ_BUF_EMPTY;
    int rc = chrecv(cmd_ch, &arg, sizeof(arg), -1);
    if (rc != 0) return;

    printf("youtube: playing '%s'\n", arg.data);

    struct mz_buf cmd = MZ_BUF_EMPTY;
    while (1) {
        struct mz_buf desc = MZ_BUF_EMPTY;
        mz_buf_printf(&desc, "youtube [%d:%02d] '%s'",
                time / 60, time % 60, arg.data);

        rc = chsend(desc_ch, &desc, sizeof(desc), -1);
        if (rc != 0 && errno != ETIMEDOUT) return;

        time++;
        if (time > 120) break;

        mz_buf_free(&cmd);
        rc = chrecv(cmd_ch, &cmd, sizeof(cmd), now() + 100);
        if (rc != 0 && errno != ETIMEDOUT) return;
        if (rc != 0) continue;

        printf("youtube got cmd '%s'\n", cmd.data);
        mz_buf_free(&cmd);
    }

    printf("youtube '%s' terminating\n", arg.data);
    mz_buf_free(&arg);
}

struct mz_module mz_youtube = {
    .name = "YouTube",
    .match_fn = &youtube_match,
    .run_coro = &youtube,
};
