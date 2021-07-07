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
import pymumble_py3 as pymumble
import time
import ffmpeg
import subprocess
from threading import Thread
from pydub import AudioSegment
from .utils import Watchdog, SilenceError, ConfigurationError, parse_message

SAMPLES_PER_SECOND = 48000
NUM_CHANNELS = 1
MAX_SILENCE_DURATION = 30*1000 #30 seconds
BUFFER_DURATION = 10 # ms Must be 10ms or a multiple thereof
WATCHDOG_RATE = 5 # ms


class MumbleConnector:
    def __init__(self, server, port, username, password, channel):
        self.channel = channel
        self.mumble = pymumble.Mumble(server, username,
                                      port, password,
                                      reconnect=True)
        self.logger = logging.getLogger(__name__)
        self.silence_count = 0

    def start(self):
        self.mumble.start()
        self.mumble.is_ready()
        self.mumble.callbacks.set_callback(
            pymumble.constants.PYMUMBLE_CLBK_DISCONNECTED,
            self.start)
        self.logger.info('Mumble client started')
        channel = self.mumble.channels.find_by_name(self.channel)
        if channel == None:
            self.logger.error(f'Unable to find channel {self.channel}')
        else:
            channel.move_in()

    def stop(self):
        self.mumble.callbacks.remove_callback(
            pymumble.constants.PYMUMBLE_CLBK_DISCONNECTED,
            self.start)
        self.mumble.stop()
        self.logger.info('Disconnected from Mumble')

    def set_message_callback(self, fn):
        self.mumble.callbacks.set_callback(
            pymumble.constants.PYMUMBLE_CLBK_TEXTMESSAGERECEIVED,
            fn)

    def set_get_sound(self, receive):
        self.logger.debug('Reset silence count')
        self.silence_count = 0
        self.mumble.set_receive_sound(receive)

    def send_message(self, message):
        self.logger.debug(f'Sending message {message} to mumble channel')
        self.mumble.my_channel().send_text_message(message)

    def get_audio(self, buffer_size):
        self.logger.debug('Fetching mumble audio')
        audio_length = buffer_size/1000
        audio = AudioSegment.silent(duration=buffer_size, frame_rate=SAMPLES_PER_SECOND)
        silence = True
        for session_id, user in self.mumble.users.items():
            user_audio = user.sound
            if user_audio.is_sound():
                silence = False
                audio_data = AudioSegment(
                    data=user_audio.get_sound(audio_length).pcm,
                    sample_width=2, # bytes => 16 bit
                    frame_rate=SAMPLES_PER_SECOND,
                    channels=1
                )
                audio = audio.overlay(audio_data)
        if NUM_CHANNELS == 2:
            audio = AudioSegment.from_mono_audiosegments(audio, audio)
        if silence:
            self.logger.debug(f'Silence detected from Mumble for {buffer_size}ms')
            self.silence_count = self.silence_count + buffer_size
        else:
            self.silence_count = 0
        if self.silence_count > MAX_SILENCE_DURATION:
            self.silence_count = 0
            raise SilenceError()
        return audio.raw_data


class IcecastConnector:
    def __init__(self, server, port, username, password, mount_point):
        self.logger = logging.getLogger(__name__)
        self.icecast_string = f'icecast://{username}:{password}@{server}:{port}{mount_point}'
        self.icecast_stream = None
        self.is_connected = False

    def start(self):
        args = (
            ffmpeg
            .input('pipe:', format='s16le', ar=SAMPLES_PER_SECOND, ac=NUM_CHANNELS)
            .output(self.icecast_string,
                    codec="libmp3lame",
                    f='mp3',
                    ac=2,
                    legacy_icecast=1,
                    sample_fmt='fltp',
                    content_type='audio/mpeg',
                    **{
                        'b:a': '132k',
                    })
            .compile()
        )
        args.insert(1, '-re')
        self.icecast_stream = subprocess.Popen(args, stdin=subprocess.PIPE)
        self.logger.info('Icecast stream started')
        self.is_connected = True

    def write(self, pcm):
        if self.icecast_stream.poll():
            self.logger.warning('Icecast stream disconnected unexpectedly, reconnecting...')
            self.is_connected = False
            self.start()
        self.logger.debug('Writing data to FFMpeg')
        try:
            self.icecast_stream.stdin.write(pcm)
        except ValueError:
            self.logger.debug('Attempted to write to closed Icecast stream')
            self.is_connected = False

    def stop(self):
        if self.icecast_stream:
            self.icecast_stream.stdin.close()
        self.logger.info('Disconnected from Icecast')
        self.is_connected = False

class Bot:
    def __init__(self, mumble, icecast, command_prefix):
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
        }
        self.timer = Watchdog(WATCHDOG_RATE/1000, self.write_audio)

    def run(self):
        self.logger.debug('Starting MumbleIce bot')
        self.logger.debug('Connecting to Mumble...')
        self.mumble.start()
        self.logger.info('Connected to Mumble')
        self.logger.info('Started MumbleIce bot')
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
                self.logger.debug(f'Not recognized command: {self.command_prefix}{message.message}')
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
            self.timer.start()

    def disconnect_icecast(self):
        self.timer.stop()
        if self.icecast.is_connected:
            self.icecast.stop()
            self.mumble.send_message('Icecast streaming stopped')
            self.mumble.set_get_sound(False)
        else:
            self.mumble.send_message('Icecast already disconnected')

    def write_audio(self):
        try:
            audio = self.mumble.get_audio(BUFFER_DURATION)
            self.icecast.write(audio)
            self.timer.reset()
        except SilenceError:
            self.logger.warning(f'No audio received from Mumble for the last {MAX_SILENCE_DURATION/1000} s. Disconnecting from Icecast...')
            self.mumble.send_message(f'No audio received for the last {MAX_SILENCE_DURATION/1000} s. Disconnecting from Icecast...')
            self.disconnect_icecast()
