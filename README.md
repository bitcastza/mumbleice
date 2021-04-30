# MumbleIce

This is a mumble bot for streaming audio from a Mumble room to Icecast.

# Installing

## Development

```bash
sudo apt install python3-dev python3-pip libopus0 virtualenv
virtualenv -p python3 pyenv
pyenv/bin/pip install -r requirements.txt
cp mumbleice.conf.example mumbleice.conf
# Configure MumbleIce to connect to your mumble and icecast servers
pyenv/bin/python -m mumbleice
```
