###########################################################################
# MumbleIce is Copyright (C) 2021 Kyle Robbertze <kyle@bitcast.co.za>
#
# MumbleIce is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3, or
# any later version as published by the Free Software Foundation.
#
# MumbleIce is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with MumbleIce. If not, see <http://www.gnu.org/licenses/>.
###########################################################################
import logging
import time
from importlib.resources import files, as_file
from .mumble import MumbleConnector
from .icecast import IcecastConnector
from .utils import Watchdog, SilenceError, ConfigurationError, parse_message, BUFFER_DURATION, WATCHDOG_RATE, NUM_CHANNELS


class Bot:
    def __init__(self, mumble, icecast, command_prefix, autoconnect=False):
        if BUFFER_DURATION % 10 != 0:
            raise ConfigurationError('BUFFER_DURATION must be 10ms or a multiple thereof')
        if NUM_CHANNELS not in [1, 2]:
            raise ConfigurationError('NUM_CHANNELS must be 1 (mono) or (stereo). Other values are not supported')
        self.mumble = mumble
        self.mumble.set_message_callback(self.mumble_message)
        self.icecast = icecast
        self.logger = logging.getLogger(__name__)
        self.command_prefix = command_prefix
        self.commands = {
            'connect': self.connect_icecast,
            'disconnect': self.disconnect_icecast,
            'status': self.show_icecast_status,
        }
        self.autoconnect = autoconnect
        self.timer = Watchdog(WATCHDOG_RATE/1000, self.write_audio)

    def run(self):
        self.logger.debug('Starting MumbleIce bot')
        self.logger.debug('Connecting to Mumble...')
        self.mumble.start()
        self.logger.info('Connected to Mumble')
        self.logger.info('Started MumbleIce bot')

        if self.autoconnect:
            self.connect_icecast()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.timer.stop()
            self.icecast.stop()
            self.mumble.stop()

    def mumble_message(self, message):
        self.logger.info(f'Message received: {message.message}')
        msg = parse_message(message.message)
        if msg.startswith(self.command_prefix) and len(msg) > len(self.command_prefix):
            msg = msg[len(self.command_prefix):]
            msg = msg.split(' ')
            cmd = self.commands.get(msg[0])
            if cmd == None:
                self.logger.debug(f'Not recognized command: {message.message}')
                self.mumble.send_message('Command not recognised')
                return
            cmd()

    def connect_icecast(self):
        if self.icecast.is_connected:
            self.mumble.send_message('Icecast already connected')
        else:
            self.icecast.start()
            self.mumble.set_get_sound(True)
            self.mumble.send_message('Icecast stream started')
            audio_file = files('mumbleice').joinpath('resources').joinpath('streaming_started.wav')
            with as_file(audio_file) as audio:
                self.mumble.send_audio(audio.resolve())
            self.timer.start()

    def disconnect_icecast(self):
        self.timer.stop()
        if self.icecast.is_connected:
            self.icecast.stop()
            self.mumble.send_message('Icecast streaming stopped')
            audio_file = files('mumbleice').joinpath('resources').joinpath('streaming_stopped.wav')
            with as_file(audio_file) as audio:
                self.mumble.send_audio(audio.resolve())
            self.mumble.set_get_sound(False)
            # Ensure that the timer has stopped and will not restart
            self.timer.stop()
        else:
            self.mumble.send_message('Icecast already disconnected')

    def write_audio(self):
        try:
            audio = self.mumble.get_audio(BUFFER_DURATION)
            self.icecast.write(audio)
            self.timer.reset()
        except SilenceError:
            self.logger.warning(f'No audio received from Mumble for the last {self.mumble.max_silence} s. Disconnecting from Icecast...')
            self.mumble.send_message(f'No audio received for the last {self.mumble.max_silence} s. Disconnecting from Icecast...')
            self.disconnect_icecast()
        except BrokenPipeError:
            self.mumble.send_message('Icecast disconnected unexpectedly. Streaming stopped')
            self.disconnect_icecast()

    def show_icecast_status(self):
        if self.icecast.is_connected:
            self.mumble.send_message('Icecast is <b>connected</b> and streaming')
        else:
            self.mumble.send_message('Icecast is <b>disconnected</b> and not streaming')
