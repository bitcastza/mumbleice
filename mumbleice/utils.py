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
import re
from threading import Timer

class Watchdog(Exception):
    def __init__(self, timeout, handler=None):
        self.timeout = timeout
        if handler:
            self.handler = handler
        else:
            self.handler = self.default_handler
        self.timer = Timer(self.timeout, self.handler)

    def start(self):
        try:
            self.timer.start()
        except RuntimeError:
            self.reset()

    def reset(self):
        self.timer.cancel()
        self.timer = Timer(self.timeout, self.handler)
        self.timer.start()

    def stop(self):
        self.timer.cancel()
        self.timer = Timer(self.timeout, self.handler)

    def default_handler(self):
        raise self


class SilenceError(Exception):
    pass


class ConfigurationError(Exception):
    pass


def parse_message(message):
    message = re.sub('<[^<]+?>', '', message)
    return message.lower()
