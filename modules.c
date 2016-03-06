#include "modules.h"

static struct mz_module * modules = NULL;

int mz_module_add(struct mz_module * mod) {
    mod->next = modules;
    modules = mod;
    return 0;
}

int mz_module_remove(struct mz_module * mod) {
    for(struct mz_module * m = modules; m != NULL; m = m->next) {
        if (m->next == mod) {
            m->next = m->next->next;
            return 0;
        }
    }
    return -1;
}

struct mz_module * mz_module_match(const char * input, mz_cmd command) {
    for(struct mz_module * m = modules; m != NULL; m = m->next) {
        if (m->match_fn(input, command) == true)
            return m;
    }
    return NULL;
}
