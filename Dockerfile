# syntax=docker/dockerfile:1
FROM ubuntu:latest

RUN apt-get update && apt-get install --no-install-recommends -y gcc mosquitto mosquitto-clients build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev libbz2-dev && apt-get install wget -y

RUN rm -rf /var/lib/apt/lists/*

RUN wget https://www.python.org/ftp/python/3.7.4/Python-3.7.4.tgz && tar -xf Python-3.7.4.tgz && cd Python-3.7.4 && ./configure --enable-optimizations && make install && pip3 install ipython requests paho-mqtt && rm -rf Python-3.7.4 Python-3.7.4.tgz && apt-get remove wget build-essential -y 

COPY . .

RUN chmod +x start.sh

CMD [ "./start.sh"]
