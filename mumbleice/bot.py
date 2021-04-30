###########################################################################
# MumbleIce is Copyright (C) 2021 Kyle Robbertze <kyle@paddatrapper.com>
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
from .watchdog import Watchdog

SAMPLES_PER_SECOND = 48000
NUM_CHANNELS = 1


class MumbleConnector:
    def __init__(self, server, port, username, password, channel):
        self.channel = channel
        self.mumble = pymumble.Mumble(server, username,
                                      port, password,
                                      reconnect=True)
        self.logger = logging.getLogger(__name__)
        self.mumble.callbacks.set_callback(
            pymumble.constants.PYMUMBLE_CLBK_DISCONNECTED,
            self.start)

    def start(self):
        self.mumble.start()
        self.mumble.is_ready()
        self.logger.info('Mumble client started')
        channel = self.mumble.channels.find_by_name(self.channel)
        if channel == None:
            self.logger.warn(f'Unable to find channel {self.channel}')
        else:
            channel.move_in()

    def stop(self):
        self.mumble.stop()
        self.logger.info('Disconnected from Mumble')

    def set_message_callback(self, fn):
        self.mumble.callbacks.set_callback(
            pymumble.constants.PYMUMBLE_CLBK_TEXTMESSAGERECEIVED,
            fn)

    def set_sound_callback(self, fn):
        self.mumble.callbacks.set_callback(
            pymumble.constants.PYMUMBLE_CLBK_SOUNDRECEIVED,
            fn)

    def set_get_sound(self, receive):
        self.mumble.set_receive_sound(receive)

    def send_message(self, message):
        self.logger.debug(f'Sending message {message} to mumble channel')
        self.mumble.my_channel().send_text_message(message)


class IcecastConnector:
    def __init__(self, server, port, username, password, mount_point):
        self.logger = logging.getLogger(__name__)
        self.icecast_string = f'icecast://{username}:{password}@{server}:{port}{mount_point}'
        self.timer = Watchdog(0.5, self.write_silence)

    def start(self):
        args = (
            ffmpeg
            .input('pipe:', format='s16le', ar=SAMPLES_PER_SECOND, ac=NUM_CHANNELS)
            .output(self.icecast_string, codec="libmp3lame", f='mp3', content_type='audio/mpeg', **{'b:a': '64k'})
            .compile()
        )
        # Write silence if no audio is received from Mumble
        self.timer.start()
        self.icecast_stream = subprocess.Popen(args, stdin=subprocess.PIPE)
        self.logger.info('Icecast stream started')

    def write_silence(self):
        self.logger.debug('No audio received from Mumble, writing silence to Icecast')
        silence_audio = AudioSegment.silent(duration=500, frame_rate=SAMPLES_PER_SECOND)
        if NUM_CHANNELS == 2:
            silence_audio = AudioSegment.from_mono_audiosegments(silence_audio, silence_audio)
        self.write(silence_audio.raw_data)

    def write(self, pcm):
        self.timer.reset()
        if self.icecast_stream.poll():
            self.logger.warning('Icecast stream disconnected unexpectedly, reconnecting...')
            self.start()
        self.logger.debug('Writing data to FFMpeg')
        self.icecast_stream.stdin.write(pcm)

    def stop(self):
        self.timer.stop()
        self.icecast_stream.stdin.close()
        self.logger.info('Disconnected from Icecast')

class Bot:
    def __init__(self, mumble, icecast, command_prefix):
        self.mumble = mumble
        self.mumble.set_message_callback(self.mumble_message)
        self.mumble.set_sound_callback(self.send_sound_chunk)
        self.icecast = icecast
        self.logger = logging.getLogger(__name__)
        self.command_prefix = command_prefix
        self.commands = {
            'connect': self.connect_icecast,
            'disconnect': self.disconnect_icecast,
        }

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
            self.icecast.stop()
            self.mumble.stop()

    def mumble_message(self, message):
        self.logger.info(f'Message received: {message.message}')
        msg = message.message
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
        self.icecast.start()
        self.mumble.set_get_sound(True)
        self.mumble.send_message('Icecast stream started')

    def disconnect_icecast(self):
        self.icecast.stop()
        self.mumble.send_message('Icecast streaming stopped')
        self.mumble.set_get_sound(False)

    def send_sound_chunk(self, user, sound_chunk):
        self.logger.debug('Received Mumble sound chunk')
        self.icecast.write(sound_chunk.pcm)
