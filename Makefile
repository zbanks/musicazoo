CC=gcc
CFLAGS=-I. -Inanomsg/src/ -Ilibdill -g -O2 -std=gnu99 -Wall -Wextra -Werror
LDFLAGS=-ldill -lnanomsg -ljansson

OBJECTS=fake_youtube.o volume.o web.o modules.o queue.o util.o main.o
TARGET=musicazoo

%.o : %.c
	$(CC) $(CFLAGS) -c $< -o $@

$(TARGET) : $(OBJECTS)
	$(CC) $^ $(CFLAGS) $(LDFLAGS) -o $@

.PHONY: clean
.DEFAULT: all

clean:
	-rm -r $(OBJECTS) $(TARGET)

all: $(TARGET)

