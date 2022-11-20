FROM python:3.11

RUN apt-get update -qq && apt-get upgrade -y -qq
RUN apt-get install -y -qq libopus0 ffmpeg

ENV MUMBLEICE_CONFIG_FILE=/mumbleice.yml

COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/mumbleice.yml /mumbleice.yml

WORKDIR /app

COPY requirements.txt ./

RUN pip3 install -U pip
RUN pip3 install --no-cache-dir -r requirements.txt

COPY ./ /app
CMD /entrypoint.sh
