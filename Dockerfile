# syntax=docker/dockerfile:1
FROM python:3.7.13-bullseye

RUN apt-get update && apt-get install --no-install-recommends -y mosquitto mosquitto-clients && apt-get install wget -y

RUN rm -rf /var/lib/apt/lists/*

RUN pip3 install ipython requests paho-mqtt

COPY . .

RUN chmod +x start.sh

CMD [ "./start.sh"]
