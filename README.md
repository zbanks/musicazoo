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
./run_musicazoo.sh settings.json
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
python -m shmooze.wsgi
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

First, install musicazoo. Although you can install it from pip, it is easier to configure by cloning from git:

```
git clone https://github.com/zbanks/musicazoo.git
cd musicazoo
pip install -r requirements.txt
```

Installing from git makes it easier to configure your system. 

Now, edit `supervisord.conf` and `settings.json`. Although the given configurations will work out of the box, you may want to disable supervisord's web interface (or at least change the password). The name/colors can be changed in `settings.json`. 

Once everything is configured, run:

```
sudo python setup.py install
```

And test your installation by running `musicazoo` and navigating to [http://localhost:8080/index.html](http://localhost:8080/index.html). 

### Running Musicazoo on startup

Running the supervisord daemon on startup depends on your system. There are a collection of scripts for many systems available [here](https://github.com/Supervisor/initscripts). There is general advice for configuring supervisord for Linux available [here](http://serverfault.com/questions/96499/how-to-automatically-start-supervisord-on-linux-ubuntu).

You will likely need to symlink or copy your `supervisord.conf` to `/etc/supervisor/supervisord.conf` and make sure that the `pidfile` in `supervisord.conf` corresponds to `PIDFILE` in your init script.
