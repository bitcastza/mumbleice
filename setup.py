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
from setuptools import setup, find_packages

setup(
    name='mumbleice',
    version='1.0.1',
    description='Mumble bot for streaming to Icecast',
    long_description='A Mumble bot that will stream a room to a pre-configured icecast mount-point',
    url='https://gitlab.com/bitcast/mumbleice',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Other Audience',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Communications',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Environment :: Console',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='mumble audio icecast streaming',
    packages=find_packages(),
    install_requires=[
        'pymumble',
        'ffmpeg-python',
        'pydub',
        'pyaml-env',
    ],
    entry_points={
        'console_scripts': ['mumbleice=mumbleice.__main__:run'],
    },
    package_data={
        'pymumble': [
            'LICENCE.md',
            'mumbleice.yml.example',
        ],
    },
)
