#ifndef __MUSICAZOO_QUEUE__
#define __MUSICAZOO_QUEUE__

#include <libdill.h>

#include "modules.h"

struct mz_item {
    int id;
    bool running;
    const char * desc;
};

int mz_queue_add(const char * command);
int mz_queue_cmd(int id, const char * command, uint64_t deadline);
struct mz_item * mz_queue_get(int id);

void mz_queue_close();

struct mz_item * mz_queue_head();
void mz_queue_next(struct mz_item ** iter);

#endif
