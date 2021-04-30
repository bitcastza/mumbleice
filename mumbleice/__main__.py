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
import argparse
import configparser
import logging
import sys

from .bot import Bot, IcecastConnector, MumbleConnector

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',
                        help='the configuration file to use',
                        default='mumbleice.conf')
    parser.add_argument('-v', '--verbose',
                        help='show debug information',
                        action='store_true')
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger(__name__)
    try:
        config = configparser.ConfigParser()
        config.read(args.config)

        cfg = config['mumble']
        mumble = MumbleConnector(cfg['server'], cfg.getint('port'),
                                 cfg['username'], cfg['password'],
                                 cfg['channel'])
        cfg = config['icecast']
        icecast = IcecastConnector(cfg['server'], cfg.getint('port'),
                                   cfg['username'], cfg['password'],
                                   cfg['mount-point'])

        bot = Bot(mumble, icecast, config['mumble']['command-prefix'])
        bot.run()
    except KeyError:
        logger.error('Error reading config file')
        parser.print_help(file=sys.stderr)
        exit(1)
