FROM python:3.11.4-slim-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
dnsutils \
telnet \
curl \
procps \
gcc \
lsb-release \
gnupg2 && \
apt-get -y autoremove && \
apt-get clean

RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
curl -sSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
apt-get update && \
apt-get install -y --no-install-recommends \
libc-dev \
libpq-dev \
postgresql-client-15 && \
apt-get -y autoremove && \
apt-get clean

RUN groupadd -r python && useradd --create-home -g python python

USER python
ENV PATH="/home/python/.local/bin:${PATH}"
RUN pip install --upgrade pip
RUN mkdir /home/python/battery
WORKDIR /home/python/battery

COPY --chown=python . .

RUN pip install --user -r requirements.txt

CMD ["python", "/home/python/battery/app.py"]
