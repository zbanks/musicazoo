#ifndef __MUSICAZOO_MUSICAZOO_H__
#define __MUSICAZOO_MUSICAZOO_H__

#include <libdill.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#define MZ_CMD_SIZE 2048
#define __STRINGIFY2(x) # x
#define __STRINGIFY(x) __STRINGIFY2(x)
#define MZ_CMD_SIZE_STR __STRINGIFY(MZ_CMD_SIZE)

typedef char mz_cmd[MZ_CMD_SIZE];

#define MZ_PERROR() fprintf(stderr, __FILE__ ":" __STRINGIFY(__LINE__) " errno: %s\n", strerror(errno))

#include "queue.h"
#include "modules.h"

#endif
