Musicazoo
=========


## Setup:

```
git clone https://github.com/zbanks/musicazoo.git
cd musicazoo
pip install -r requirements.txt
```

## New Debathena Server Setup:

```
sudo apt-get install git vlc python-imaging-tk python-dev libasound2-dev nginx alsa-base xorg
sudo pip install --upgrade pip
git clone https://github.com/zbanks/musicazoo.git
cd musicazoo
sudo pip install -r requirements.txt
sudo rm /etc/nginx/sites-enabled/default
sudo ln -s $PWD/nginx.conf /etc/nginx/sites-available/musicazoo
sudo ln -s /etc/nginx/sites-available/musicazoo /etc/nginx/sites-enabled/musicazoo

# Now edit configuration files
# Change /home/musicazoo/musicazoo/www/ to /<INSTALL_PATH>/musicazoo/www/
nano nginx.conf 
# Tweak settings (Set name)
nano musicazoo/settings.py

# Test
python musicazoo/mzserver.py --debug
```

### Running Debug Server

```
musicazoo/mzserver.py --debug

```

Now point a web browser to http://localhost:9000

### Potential additional dependencies
python-pip
python-imaging-tk
python-dev
