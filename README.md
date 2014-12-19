Musicazoo
=========

## Quickstart (PIP)
```
sudo pip install musicazoo
musicazoo
```
Navigate to [http://localhost:8080/index.html](http://localhost:8080/index.html) in a web browser.
Alternatively, from the command line:
```
mz help
```

## Setup
```
git clone https://github.com/zbanks/musicazoo.git
cd musicazoo
pip install -r requirements.txt
```

## Run without installing
```
. init.sh
./run_musicazoo.sh
```

## Debugging

Musicazoo is split into several services:
* Web server (a WSGI object)
* Queue (handles life, death, and control of modules)
* Volume (handles volume control)
* NLP (exposes a plain-text command interface)

It is probably helpful to debug these without supervisor, in which case you should simply run each one in a separate terminal.

```
. init.sh
python -m musicazoo.wsgi
python -m musicazoo.queue
python -m musicazoo.volume
python -m musicazoo.nlp
```

The WSGI service exposes several JSON endpoints. By default:
 * /queue
 * /vol
 * /nlp

It also puts up up the static web interface at [http://localhost:8080/index.html](http://localhost:8080/index.html).

You can interact with the JSON endpoints directly using `debug/raw.py`.

Alternatively, you can interact with the NLP endpoint using the `mz` command-line tool.

## Installing
Right now you can use PIP. More details coming soon!

## Setting up as a service
Coming soon!
