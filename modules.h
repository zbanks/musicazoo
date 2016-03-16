#ifndef __MUSICAZOO_MODULES_H__
#define __MUSICAZOO_MODULES_H__

#include "musicazoo.h"

typedef bool (*mz_module_match_fn)(const char * input, struct mz_buf * command);
typedef void (*mz_module_run_coro)(int cmd_ch, int desc_ch);

struct mz_module;
struct mz_module {
    const char * name;
    mz_module_match_fn match_fn;
    mz_module_run_coro run_coro;

    // private
    struct mz_module * next;
};

int mz_module_add(struct mz_module * module);
int mz_module_remove(struct mz_module * module);

struct mz_module * mz_module_lookup(const char * name);
struct mz_module * mz_module_match(const char * input, struct mz_buf * command);

extern struct mz_module mz_youtube;
extern struct mz_module mz_volume;

#endif
