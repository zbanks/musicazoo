#include "musicazoo.h"
#include <assert.h>

int main(void) {
    int rc = 0;
    mz_module_add(&mz_youtube);

    rc = mz_queue_add("youtube hello world!");
    assert(rc == 0);

    for (int i = 0; i < 10; i++) {
        int rc = 0;
        if (i == 3)
            rc = mz_queue_add("youtube california gurlz");
        if (i == 5)
            rc = mz_queue_cmd(1, "skip", 0);
        assert(rc == 0);

        int idx = 1;
        for (struct mz_item * item = mz_queue_head(); item != NULL; mz_queue_next(&item)) {
            printf("%d. %s\n", idx++, item->desc);
        }
        printf("\n");

        msleep(now() + 200);
    }

    mz_queue_close();
    return 0;
}
