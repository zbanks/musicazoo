CC=gcc
CFLAGS=-I. -Ilibdill -g -O2 -std=gnu99 -Wall -Wextra -Werror
LDFLAGS=-ldill

OBJECTS=fake_youtube.o modules.o queue.o main.o
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

