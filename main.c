#include "musicazoo.h"
#include "web.h"
#include <assert.h>
#include <jansson.h>

int main(void) {
    int rc = 0;
    mz_module_add(&mz_youtube);
    mz_module_add(&mz_volume);

    int pub_ch = channel(sizeof(struct mz_buf), 1);
    mz_web_bind("ws://*:6555", "ws://*:6556", pub_ch);

    rc = mz_queue_add_static("Volume", "1");
    assert(rc == 0);

    rc = mz_queue_add("youtube hello world!");
    assert(rc == 0);

    for (int i = 0; i < 10; i++) {
        uint64_t deadline = now() + 1000;

        int rc = 0;
        if (i == 3)
            rc = mz_queue_add("youtube california gurlz");
        if (i == 5)
            rc = mz_queue_cmd(1, "skip", 0);
        assert(rc == 0);

        json_t * queue = json_array();
        //int idx = 1;
        for (struct mz_item * item = mz_queue_head(); item != NULL; mz_queue_next(&item)) {
            json_array_append_new(queue, json_pack("{sisssiss}", 
                        "id", item->id,
                        "module", item->module_name,
                        "last_update", (int) (item->desc_time / 1000),
                        "description", item->desc.data));

        }
        struct mz_buf pub_buf = MZ_BUF_EMPTY;
        pub_buf.free_ptr = pub_buf.data = json_dumps(queue, JSON_INDENT(4));
        pub_buf.len = strlen(pub_buf.data);

        //printf("%s\n\n", pub_buf.data);
        rc = chsend(pub_ch, &pub_buf, sizeof pub_buf, deadline);
        if (rc < 0 && errno != ETIMEDOUT) {
            printf("Error publishing queue status; quitting\n");
            break;
        }

        yield();
        msleep(deadline);
    }

    mz_queue_close();
    mz_web_close();

    return 0;
}
