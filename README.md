# MumbleIce

This is a mumble bot for streaming audio from a Mumble room to Icecast.

# Installing

## Production (Docker)
The Docker image is recommended for running in production. The configuration
file should be mounted to `/mumbleice.conf`. The file location can be changed
with the `MUMBLEICE_CONFIG_FILE` environment variable.

```bash
docker run -v $(pwd)/mumbleice.conf:/mumbleice.conf bitcast/mumbleice:dev
```

## Development

```bash
sudo apt install python3-dev python3-pip libopus0 virtualenv
virtualenv -p python3 pyenv
pyenv/bin/pip install -r requirements.txt
cp mumbleice.conf.example mumbleice.conf
# Configure MumbleIce to connect to your mumble and icecast servers
pyenv/bin/python -m mumbleice
```
