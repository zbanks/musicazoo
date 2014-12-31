# Musicazoo Example Interaction

Let's now examine how a Youtube video behaves when added over the command-line interface.

For exampe, you might type: 

`mz anaconda`

to play Nicki Minaj's "Anaconda."

The command-line interfaces has very little intelligence, and basically passes all of its argumts to the NLP endpoint. So, the following JSON message gets sent via an HTTP POST request to `/nlp`.

`{"cmd": "do","args": {"message": "anaconda"}}`

The WSGI service decodes this, ensures that it is indeed proper JSON, and passes the message unchanged to the NLP service over its raw JSON pipe (TCP addresses for all of these pipes can be found in `musicazoo/wsgi/endpoints.py`.)

The NLP service parses the message, and since it doesn't match any known command, it searches YouTube for the provided string, retrieving the video URL. It then passes the following JSON to the queue over its raw pipe: 

`{"cmd": "add","args": {"type": "youtube","args": {"url": "https: //www.youtube.com/watch?v=LDZX4ooRsWs"}}}`

The queue parses this command, and spawns a new process: the YouTube module. It opens the two pipes to the module: command and update. It then passes initialization information over the command pipe as follows: 

`{"cmd": "init","args": {"url": "https: //www.youtube.com/watch?v=LDZX4ooRsWs"}}`

The YouTube module now begins the process of requesting video metadata. As this becomes available, the queue is informed of it over the update pipe. For example, once the title is known, the following update might be seen: 

`{"cmd": "set_parameters", "args": {"parameters": {"title": "Nicki Minaj - Anaconda"}}}`

Assuming that this video is now the only module on the queue, a *play* command gets sent over the command pipe: 

`{"cmd": "play"}`

The Youtube module would then begin playing the video and sending updates containing playback time, etc.
