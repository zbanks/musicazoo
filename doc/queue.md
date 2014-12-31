# All About the Queue

## Basics

The Queue can be considered the core service in Musicazoo. It handles playing videos, reading text, etc, through the use of *modules*.

The entry point for the queue is in `musicazoo/queue/__main__.py` and can be run with the command `python -m musicazoo.queue`. 

The WSGI service puts the queue on the endpoint `/queue`.

## Code Structure

Most of the intelligence for the queue is stored in `musicazoo/queue/__init__.py`. `__main__` creates a single instance of the class *Queue*.

The *Queue* class has two parents: one is *Service*, which sets up an incoming command pipe using tornado. The second is *JSONCommandProcessor* which provides standard behavior for incoming JSON messages. Specifically, it looks for incoming JSON with this format:

`{"cmd": "...","args": {...}}`

and calls handler functions based on the command string. This mapping is specified in a dict named `commands` (overridden in *Queue*.) The result is returned as follows:

`{"success": true, "result": ...}` if the function returned without error, or

`{"success": false, "error": ...}` if the function raised an error.

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
