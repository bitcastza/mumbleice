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
import ffmpeg
import subprocess
from .utils import SAMPLES_PER_SECOND, NUM_CHANNELS


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
            .global_args('-hide_banner')
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
        except BrokenPipeError as e:
            self.logger.warning('Icecast disappeared unexpectedly')
            self.disconnect_icecast()
            raise e

    def stop(self):
        if self.icecast_stream:
            self.icecast_stream.stdin.close()
        self.logger.info('Disconnected from Icecast')
        self.is_connected = False
