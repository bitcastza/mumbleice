from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='mumbleice',
    description='Mumble bot for streaming to Icecast',
    long_description=long_description,
    long_description_content_type="text/markdown",
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
