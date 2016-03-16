#include "queue.h"

static struct mz_item * queue_head = NULL;
static struct mz_item * queue_tail = NULL;

static int next_id = 1;

static void mz_queue_kill(struct mz_item * item);

static void mz_queue_check(struct mz_item ** item_p) {
    struct mz_item * item = *item_p;
    while (item != NULL) {
        struct mz_buf desc = MZ_BUF_EMPTY;
        int rc = chrecv(item->desc_chan, &desc, sizeof(desc), now() + 10);
        if (rc == 0) {
            // We got a valid descriptoion; copy it into the buffer
            mz_buf_free(&item->desc);
            memcpy(&item->desc, &desc, sizeof desc);
            item->desc_time = now();
            break;
        }
        if (errno == ETIMEDOUT) break;
        if (errno == EINVAL) {
            printf("Invalid arguments to chrecv");
            break;
        }
        if (errno == ECANCELED) {
            struct mz_item * next = item->next;
            mz_queue_kill(item);
            item = next;
        }
    }
    *item_p = item;
}

struct mz_item * mz_queue_head() {
    mz_queue_check(&queue_head);
    return queue_head;
}

void mz_queue_next(struct mz_item ** item_p) {
    *item_p = (*item_p)->next;
    mz_queue_check(item_p);
}

void mz_queue_close() {
    while (queue_head)
        mz_queue_kill(queue_tail);
}

static void mz_queue_kill(struct mz_item * item) {
    chdone(item->cmd_chan);
    chdone(item->desc_chan);
    hclose(item->handle);

    if (item->prev) item->prev->next = item->next;
    else queue_head = item->next;
    if (item->next) item->next->prev = item->prev;
    else queue_tail = item->prev;
}

static int mz_queue_add_module(struct mz_module * module, struct mz_buf * args) {
    struct mz_item * item = calloc(1, sizeof *item);
    if (item == NULL) return -1;

    item->desc = MZ_BUF_EMPTY;
    item->module_name = module->name;

    item->cmd_chan = channel(sizeof(struct mz_buf), 1024);
    item->desc_chan = channel(sizeof(struct mz_buf), 1);
    if (item->cmd_chan < 0 || item->desc_chan < 0) goto fail;

    int rc = chsend(item->cmd_chan, args, sizeof(struct mz_buf), 0);
    if (rc != 0) goto fail;

    item->handle = go(module->run_coro(item->cmd_chan, item->desc_chan));
    if (item->handle < 0) goto fail;

    // Add onto global queue at the end
    item->id = next_id++;
    item->next = NULL;
    item->prev = queue_tail;
    if (queue_tail != NULL) queue_tail->next = item;
    queue_tail = item;
    if (queue_head == NULL) queue_head = item;

    return 0;

fail:
    printf("Unable to open subprocess\n");
    chdone(item->cmd_chan);
    chdone(item->desc_chan);
    return -1;
}

int mz_queue_add(const char * command) {
    struct mz_buf args = MZ_BUF_EMPTY;
    struct mz_module * module = mz_module_match(command, &args); 
    if (module == NULL) return (errno = EINVAL), -1;

    return mz_queue_add_module(module, &args);
}

int mz_queue_add_static(const char * name, const char * command) {
    struct mz_module * module = mz_module_lookup(name);
    if (module == NULL) return (errno = EINVAL), -1;
    struct mz_buf args = MZ_BUF_EMPTY;
    mz_buf_printf(&args, "%s", command);

    return mz_queue_add_module(module, &args);
}

int mz_queue_cmd(int id, const char * command, uint64_t deadline) {
    for (struct mz_item * item = mz_queue_head(); item != NULL; mz_queue_next(&item)) {
        if (item->id != id) continue;
            
        struct mz_buf buffer = MZ_BUF_EMPTY;
        mz_buf_printf(&buffer, "%s", command);

        int rc = chsend(item->cmd_chan, &buffer, sizeof(buffer), deadline);
        if (rc != 0 && errno == EPIPE) mz_queue_kill(item);
        return rc;
    }
    return (errno = EINVAL), -1;
}
