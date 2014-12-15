Musicazoo
=========

## Quickstart
```
sudo pip install musicazoo
musicazoo
```
then, navigate to [http://localhost:8080/index.html](http://localhost:8080/index.html) in a web browser.
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
./musicazoo.sh
```

Now point a web browser to http://localhost:8080

## Debugging

Musicazoo is split into several parts:
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

You may also find `debug/raw.py` useful.

## Installing
Coming soon!
