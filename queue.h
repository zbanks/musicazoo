#ifndef __MUSICAZOO_QUEUE__
#define __MUSICAZOO_QUEUE__

#include <libdill.h>

#include "modules.h"

struct mz_item {
    int id;
    bool running;

    struct mz_buf desc;
    uint64_t desc_time;
    const char * module_name;

    struct mz_item * prev;
    struct mz_item * next;
    int handle;
    int cmd_chan;
    int desc_chan;
};

int mz_queue_add(const char * command);
int mz_queue_add_static(const char * name, const char * command);
int mz_queue_cmd(int id, const char * command, uint64_t deadline);
struct mz_item * mz_queue_get(int id);

void mz_queue_close();

struct mz_item * mz_queue_head();
void mz_queue_next(struct mz_item ** iter);

#endif
