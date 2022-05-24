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
from pydub import AudioSegment
from .utils import SilenceError, SAMPLES_PER_SECOND, NUM_CHANNELS, MAX_SILENCE_DURATION, read_file_buffer
import subprocess


class MumbleConnector:
    def __init__(
        self,
        server,
        port,
        username,
        password,
        channel,
        max_silence=MAX_SILENCE_DURATION,
    ):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.channel = channel
        self.mumble = pymumble.Mumble(server, username,
                                      port, password,
                                      reconnect=True)
        self.logger = logging.getLogger(__name__)
        self.silence_count = 0
        self.max_silence = max_silence * 1000 # ms

    def start(self):
        self.mumble.start()
        self.mumble.is_ready()
        #TODO: Crashes with RuntimeError("threads can only be started once")
        self.mumble.callbacks.set_callback(
            pymumble.constants.PYMUMBLE_CLBK_DISCONNECTED,
            self.restart)
        self.logger.info('Mumble client started')
        try:
            channel = self.mumble.channels.find_by_name(self.channel)
            channel.move_in()
        except pymumble.errors.UnknownChannelError:
            self.logger.error(f'Unable to find channel {self.channel}')

    def restart(self):
        self.mumble = pymumble.Mumble(self.server, self.username,
                                      self.port, self.password,
                                      reconnect=True)
        self.silence_count = 0
        self.start()

    def stop(self):
        self.mumble.callbacks.remove_callback(
            pymumble.constants.PYMUMBLE_CLBK_DISCONNECTED,
            self.restart)
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

    def send_audio(self, path):
        with read_file_buffer(path, 1024) as buffer:
            for audio in buffer:
                self.mumble.sound_output.add_sound(audio)

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

        if self.max_silence > 0:
            if silence:
                self.logger.debug(f'Silence detected from Mumble for {buffer_size}ms')
                self.silence_count = self.silence_count + buffer_size
            else:
                self.silence_count = 0
            if self.silence_count > self.max_silence:
                self.silence_count = 0
                raise SilenceError()
        return audio.raw_data
