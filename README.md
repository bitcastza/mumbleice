# MumbleIce

This is a mumble bot for streaming audio from a Mumble room to Icecast.

# Installing

## Production (Docker)
The Docker image is recommended for running in production. The configuration
file can be mounted to `/mumbleice.yml` or configuration can be done using
environment variables. The file location can be changed with the
`MUMBLEICE_CONFIG_FILE` environment variable.

All configuration options can be set using environment variables:

```bash
docker run -e MUMBLE_SERVER=mumble.server bitcast/mumbleice:dev
```

### Environment Variables

* **MUMBLE_SERVER**: The Mumble server to connect to.
* **MUMBLE_PORT**: The port which the Mumble server uses. Defaults to `64738`.
* **MUMBLE_USERNAME**: The username for the bot on Mumble. Defaults to
  `live-streamer`.
* **MUMBLE_PASSWORD**: The server password.
* **MUMBLE_CHANNEL**: The Mumble channel to join. Defaults to `Root`.
* **MUMBLE_COMMAND_PREFIX**: The command prefix that identifies commands to the
  bot. Defaults to `!`.
* **ICECAST_SERVER**: The Icecast server to connect to.
* **ICECAST_PORT**: The port which the Icecast server uses. Defaults to `8000`.
* **ICECAST_USERNAME**: The username to authenticate against Icecast with.
  Defaults to `source`.
* **ICECAST_PASSWORD**: The password to authenticate against Icecast with.
  Defaults to `hackme`.
* **ICECAST_MOUNT_POINT**: The mount point to use for streaming audio. Defaults
  to `/mumble`.

## Development

```bash
sudo apt install python3-dev python3-pip libopus0 virtualenv
virtualenv -p python3 pyenv
pyenv/bin/pip install -e .
cp mumbleice.yml.example mumbleice.yml
# Configure MumbleIce to connect to your mumble and icecast servers
pyenv/bin/mumbleice
```
