Musicazoo
=========


## Setup

```
git clone https://github.com/zbanks/musicazoo.git
cd musicazoo
pip install -r requirements.txt
```

## Run
. init.sh
./musicazoo.sh
```

Now point a web browser to http://localhost:8080

## Debugging

Musicazoo is split into several parts:
* Web server (a WSGI object)
* Queue (handles life, death, and control of modules)
* Volume (handles volume control)

It is probably helpful to debug these without supervisor, in which case you should simply run each one in a separate terminal.

```
. init.sh
python musicazoo/wsgi
python musicazoo/queue
python musicazoo/volume
```

You may also find debug/raw.py useful.
