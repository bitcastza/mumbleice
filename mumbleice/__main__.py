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
import argparse
import logging
import os
import sys

from pyaml_env import parse_config, BaseConfig
from .bot import Bot, IcecastConnector, MumbleConnector

LOGGING_FORMAT = '%(asctime)s - %(levelname)s (%(name)s): %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',
                        help='the configuration file to use',
                        default=os.environ.get('MUMBLEICE_CONFIG_FILE', 'mumbleice.yml'))
    parser.add_argument('-v', '--verbose',
                        help='show debug information',
                        action='store_true')
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format=LOGGING_FORMAT, datefmt=DATE_FORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT, datefmt=DATE_FORMAT)

    logger = logging.getLogger(__name__)
    try:
        if not os.path.isfile(args.config):
            raise FileNotFoundError()
        config = BaseConfig(parse_config(args.config))

        cfg = config.mumble
        mumble = MumbleConnector(cfg.server, int(cfg.port),
                                 cfg.username, cfg.password,
                                 cfg.channel, int(cfg.max_silence))
        cfg = config.icecast
        icecast = IcecastConnector(cfg.server, int(cfg.port),
                                   cfg.username, cfg.password,
                                   cfg.mount_point)

        # Required because pyaml_env environment variables are returned as
        # strings, regardless of actual type
        autoconnect = str(config.icecast.autoconnect).lower() in ['true', 'yes']
        bot = Bot(mumble, icecast, config.mumble.command_prefix, autoconnect)
        bot.run()
    except KeyError:
        logger.error('Error reading config file')
        parser.print_help(file=sys.stderr)
        exit(1)
    except FileNotFoundError:
        logger.error(f'Config file {args.config} does not exist')
        parser.print_help(file=sys.stderr)
        exit(1)

if __name__ == '__main__':
    run()
