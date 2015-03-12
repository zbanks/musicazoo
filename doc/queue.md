# All About the Queue

## Basics

The Queue can be considered the core service in Musicazoo. It handles playing videos, reading text, etc, through the use of *modules*.

The entry point for the queue is in `musicazoo/queue/__main__.py` and can be run with the command `python -m musicazoo.queue`. 

The WSGI service puts the queue on the endpoint `/queue`.

## Code Structure

Most of the intelligence for the queue is stored in `musicazoo/queue/__init__.py`. `__main__` creates a single instance of the class *Queue*.

The *Queue* class has two parents: one is *Service*, which sets up an incoming command pipe using tornado. The second is *JSONCommandProcessor* which provides standard behavior for incoming JSON messages. Specifically, it looks for incoming JSON with this format:

`{"cmd": "...", "args": {...}}`

and calls handler functions based on the command string. This mapping is specified in a dict named `commands` (overridden in *Queue*.) The result is returned as follows:

`{"success": true, "result": ...}` if the function returned without error, or

`{"success": false, "error": ...}` if the function raised an error.

A lot of services, including Queue, are single-threaded and manage concurrency using [tornado](http://tornado.readthedocs.org/en/latest/coroutine.html). It would be wise if you are working with the Queue itself to learn and understand how tornado works, and how coroutines work. Any blocking call in Queue will stall the queue for all clients and modules, and any crash in Queue will take down all modules. Because Queue is so fragile, its code has been written very carefully, and most of the functionality has been moved into short-lived child processes called *modules* (see below).

## Commands

### add / set_bg

The *add* command adds a module to the end of the queue. It takes two arguments: `type` is a string identifying the type of module to create, and `args` is a dictionary of instantiation arguments. It returns a dict with one element, `uid`, which indicates the UID of the newly created module.

For example, to create a new youtube video:

```
{"cmd": "add", "args":
    {"type": "youtube","args": {"url": "https: //www.youtube.com/watch?v=LDZX4ooRsWs"}}
}
```

The elements in the second `args` dict will vary based on the module being constructed.

The *set_bg* command behaves identically, except the specified module will be set as the background rather than added to the queue. If a background exists, it will be removed and replaced.

### queue / bg

The *queue* command retrieves infomation about the queue. It takes one optional argument: `parameters`, which describes what information should be retrieved. If `parameters` is omitted, only types and UIDs are retrieved. For example:

`{"cmd": "queue"}` might return

```
{"success": true, "result":
    [{"uid": 1, "type": "youtube"},
     {"uid": 2, "type": "text"}]
}
```

If more information is desired, it can be specified in the `parameters` dict. For example, if you wanted to retrieve the "title" and "duration" of any youtube module, as well as the "text" for any text module, you could issue the following command:

```
{"cmd": "queue", "args": {
    "parameters": {
        "youtube": ["title", "duration"],
        "text": ["text"]
    }
}}
```

This query might return:
```
{"success": true, "result": [
    {"uid": 1, "type": "youtube", "title": "Nicki Minaj - Anaconda", "duration": 289.599},
    {"uid": 2, "type": "text", "text": "Hello, World!"}
]}
```

The return type is always a list, but may be empty. Parameters that do not exist will not appear in that module's dictionary. For available parameters, consult the code for the module in question. Note that parameters may pop into and out of existance, so all code that queries the queue must be robust against missing parameters.

The *bg* command is the same as the *queue* command, except that it queries the current background rather than the queue. It therefore returns a single dict rather than a list. If there is no background it returns `null`.

### rm

The *rm* command takes in one argument named `uids` which is a list. There is no return value. It removes all of the given modules from the queue. For example:

`{"cmd": "rm", "args": {"uids": [0]}}` removes module with UID 0 from the queue.

### mv

The *mv* command takes in one argument named `uids` which is a list. There is no return value. It reorders the current modules on the queue to match the given list. Any modules that exist and are not specified in the list are appended to the end with their ordering unchanged. For example, if the queue looks like:

`[1, 2, 3, 4]`

and the following command is issued:

`{"cmd": "mv", "args": {"uids": [3, 2, 1]}}`

then the queue would look like:

`[3, 2, 1, 4]`

### modules_available / backgrounds_available

The *modules_available* command takes no arguments. It returns a list of module names. All of these module names are valid additions to the queue. It returns no other information, and it is up to the client to know how to properly instantiate a specific module through use of the *add* command.

Example transaction:

`{"cmd": "modules_available"}`

`{"success": true, "result": ["text", "youtube"]}`

The *backgrounds_available* command behaves the same way, except it returns modules which may be set as backgrounds using the *set_bg* command.

### tell_module / tell_background

The *tell_module* command issues a command to a specified module. It takes three arguments: the UID of the module to talk to, the command, and an optional argument list to the command. These commands are module-specific. For information on what commands a module understands, consult its code.

For example, to seek ahead five seconds in video 0:

```
{"cmd": "tell_module", "args": {
    "uid": 0,
    "cmd": "seek_rel",
    "args": {"delta": 5}
}}
```

It is up to the client to know what commands are availble on which modules.

It is important to note that *tell_module* causes a "push" transaction from the queue process to its child module process. A poorly behaved child process may cause anything from a delayed response or garbage data to triggering module removal.

The *tell_background* command behaves the same way, but is for talking to the background instead. Note that it still has the UID field. This field exists as a safeguard against concurrency problems if one client tries to tell the background something without realizing that another client has recently changed out the background.

### ask_module / ask_background

The *ask_module* command is very similar to the *queue* command, except it retrieves information about a specific module rather than the entire queue. It takes two arguments, the UID of the module to query, and an optional parameters dict. For a description of the parameters dict, see the *queue* command.

If module 0 is a text module, then

```
{"cmd": "ask_module", "args": {
    "uid": 0,
    "parameters": {
        "youtube": ["title", "duration"],
        "text": ["text"]
    }
}}
```

might return

```
{"success": true, "result":
     {"uid": 0, "type": "text", "text": "Hello, World!"}
}
```

See *queue* for more information.

The *ask_module* command does not cause a transaction between the queue process and its child process. Rather, it retrieves cached information straight out of the queue process. It is the module's responsibility to push relevant information to the queue over the *update pipe*. This way, *ask_module* commands (and *queue* commands) can be fast and return immediately, since there will inevitably be a lot of them as clients poll for state changes.

*ask_background* behaves identically except that it queries the background module rather than a queue module. Again, the UID field is required as explained in *tell_background*.

## Modules

The Queue instance stores the current modules in a Python list. Each element of this list is an instance of the *Module* class, defined in `musicazoo/queue/module.py`. This object implements very little functionality. Its purpose is to serve as an interface to the child process which constitutes the actual module.

The child process can be any executable which adheres to the following standard:

* The last three command-line arguments to the executable are the queue hostname, the command pipe port number, and the update pipe port number. The program should open the given socket connections upon startup.
* The program sends and handles appropriate messages on these pipes (as described in this section.)

Any module which does not do these things is considered "badly-behaved" and is subject to termination when the queue detects abnormal behavior. Termination happens in three stages:

1. The module is issued a *rm* command over its command pipe (if the pipe still exists.) The queue waits for a graceful shutdown of the process.
2. If the process is still running, a SIGTERM is issued to the process, and the queue waits for it to terminate.
3. If the process is still running, a SIGKILL is issued to the process.

Any time the queue or background changes, a coroutine called *queue_updated* is called. This computes the difference between what the queue was and what it is now, and sends appropriate signals to modules. For example, some modules may have been removed and therefore need to be terminated. As a result of this, a new module may be at the top of the queue and need to be *played*. Or, a module may have been bumped off the top, and need to be *suspended*.

Every module must implement, at a minimum, the following four core commands:

* *init*, for when the module is first created
* *play*, for when the module is at the top of the queue
* *suspend*, for if the module was at the top of the queue but got moved down
* *rm*, for when the module is removed from the queue.

each module may implement additional commands, which can be called using *tell_module*. To differentiate them from the core commands, they are prefixed with `do_`. For example:

`{"cmd": "tell_module", "args": {"uid": 0, "cmd": "pause"}}`

is translated to the following before being sent over the module's command pipe:

`{"cmd": "do_pause"}`

## Command pipe commands (queue to module)

### init

### play

### suspend

### rm

