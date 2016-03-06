#include <string.h>

#include "queue.h"

struct mz_item_impl {
    struct mz_item public;
    mz_cmd desc;

    struct mz_item_impl * prev;
    struct mz_item_impl * next;
    int handle;
    int cmd_chan;
    int desc_chan;
};

static struct mz_item_impl * queue_head = NULL;
static struct mz_item_impl * queue_tail = NULL;

static int next_id = 1;

static void mz_queue_kill(struct mz_item_impl * impl);

static void mz_queue_check(struct mz_item_impl ** impl_p) {
    struct mz_item_impl * impl = *impl_p;
    while (impl != NULL) {
        int rc = chrecv(impl->desc_chan, impl->desc, sizeof(mz_cmd), now() + 10);
        if (rc == 0) break;
        if (errno == ETIMEDOUT) break;
        if (errno == EINVAL) {
            printf("Invalid arguments to chrecv");
            break;
        }
        if (errno == ECANCELED) {
            struct mz_item_impl * next = impl->next;
            mz_queue_kill(impl);
            impl = next;
        }
    }
    *impl_p = impl;
}

struct mz_item * mz_queue_head() {
    mz_queue_check(&queue_head);
    return &queue_head->public;
}

void mz_queue_next(struct mz_item ** item) {
    struct mz_item_impl * impl = 
        (struct mz_item_impl *) (*item);

    impl = impl->next;
    mz_queue_check(&impl);
    *item = &impl->public;
}

void mz_queue_close() {
    while (queue_head)
        mz_queue_kill(queue_tail);
}

static void mz_queue_kill(struct mz_item_impl * impl) {
    chdone(impl->cmd_chan);
    chdone(impl->desc_chan);
    hclose(impl->handle);

    if (impl->prev) impl->prev->next = impl->next;
    else queue_head = impl->next;
    if (impl->next) impl->next->prev = impl->prev;
    else queue_tail = impl->prev;
}

int mz_queue_add(const char * command) {
    mz_cmd args;
    struct mz_module * module = mz_module_match(command, args); 
    if (module == NULL) return (errno = EINVAL), -1;

    struct mz_item_impl * impl = calloc(1, sizeof *impl);
    if (impl == NULL) return -1;

    impl->public.desc = impl->desc;

    impl->cmd_chan = channel(sizeof(mz_cmd), 1024);
    impl->desc_chan = channel(sizeof(mz_cmd), 1);
    if (impl->cmd_chan < 0 || impl->desc_chan < 0) goto fail;

    int rc = chsend(impl->cmd_chan, args, sizeof(mz_cmd), 0);
    if (rc != 0) goto fail;

    impl->handle = go(module->run_coro(impl->cmd_chan, impl->desc_chan));
    if (impl->handle < 0) goto fail;

    // Add onto global queue at the end
    impl->public.id = next_id++;
    impl->next = NULL;
    impl->prev = queue_tail;
    if (queue_tail != NULL) queue_tail->next = impl;
    queue_tail = impl;
    if (queue_head == NULL) queue_head = impl;

    return 0;

fail:
    printf("Unable to open subprocess\n");
    chdone(impl->cmd_chan);
    chdone(impl->desc_chan);
    return -1;
    
}

int mz_queue_cmd(int id, const char * command, uint64_t deadline) {
    for (struct mz_item * item = mz_queue_head(); item != NULL; mz_queue_next(&item)) {
        if (item->id != id) continue;
            
        struct mz_item_impl * impl = 
            (struct mz_item_impl *) item;

        mz_cmd buffer;
        strncpy(buffer, command, sizeof(mz_cmd));
        int rc = chsend(impl->cmd_chan, buffer, sizeof(mz_cmd), deadline);
        if (rc != 0 && errno == EPIPE) mz_queue_kill(impl);
        return rc;
    }
    return (errno = EINVAL), -1;
}
