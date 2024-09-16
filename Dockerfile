FROM python:3.11.10-slim-bookworm AS build

WORKDIR /app

RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"

COPY requirements.txt ./
RUN pip install --no-compile --requirement requirements.txt

COPY setup.cfg setup.py pyproject.toml ./
COPY mumbleice ./mumbleice

RUN pip install --no-compile .

RUN pip uninstall -y \
      pip \
      setuptools \
    ;

FROM python:3.11.10-slim-bookworm

RUN set -eux; \
      apt-get update; \
      apt-get install -y --no-install-recommends \
        ffmpeg \
        libopus0 \
        gosu \
      ; \
      apt-get clean;

RUN set -eux; \
      groupadd -r mumbleice; \
      useradd -r -d /var/mumbleice -s /sbin/nologin -g mumbleice mumbleice;

COPY --from=build /app/venv /app/venv

COPY docker/entrypoint.sh /usr/local/bin/entrypoint
COPY docker/mumbleice.yml /etc/mumbleice/config.yml

ENV PATH="/app/venv/bin:$PATH"

ENTRYPOINT [ "entrypoint" ]
CMD [ "mumbleice", "-c", "/etc/mumbleice/config.yml" ]
