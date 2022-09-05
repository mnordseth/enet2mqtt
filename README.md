[![Actions Status](https://github.com/Th0masDB/enet2mqtt/workflows/Docker%20Image%20CI/badge.svg)](https://github.com/Th0masDB/enet2mqtt/actions)
# Enet2mqtt
Python library for communicating with the Gira / Jung eNet Smart Home Server (https://www.enet-smarthome.com/), and a mqtt forwarder to integrate eNet Smart Home devices with Home Assistant.


## Installation
### Requirements

 1. You have a mqtt broker. (Like mosquitto.)
 2. You have Home Assistant running.
 3. You know how to use docker. (or you can run it manually, if you want to, then I also think you know how to do it ;-)
 
### The installation 
You can install it two (three if you have unraid) ways:
#### 1. From prebuild ([docker hub](https://hub.docker.com/repository/docker/th0masdb14/enet2mqtt))
You can download the docker image and create the docker container by running this command (replace variables with correct information):

    sudo docker run -d -e enet_user=[ENET_USER] -e enet_pass=[ENET_PASSWORD] -e mqtt_user=[MQTT_USER] -e mqtt_pass=[MQTT_PASSWORD] -e enet_ip=[ENET_IP] -e mqtt_ip=[MQTT_BROKER_IP] -e mqtt_port=[MQTT_PORT] -e uri_scheme=[URI_SCHEME] -e verify_ssl_cert=[VERIFY_SSL_CERT] --name enet2mqtt th0masdb14/enet2mqtt:latest
 - [ENET_USER] = Your enet username
 - [ENET_PASSWORD] = Your enet password
 - [MQTT_USER] = your mqtt username of your broker
 - [MQTT_PASSWORD] = your mqtt password of your broker
 - [ENET_IP] = your enet server IP
 - [MQTT_BROKER_IP] = your mqtt broker IP
 - [MQTT_PORT] = your mqtt broker port
 - [URI_SCHEME] = http or https (defaults to http if not specified)
 - [VERIFY_SSL_CERT] = TRUE or FALSE if your enet server has an untrusted HTTPS certificate (defaults to TRUE if not specified)

That is it!
 
#### 2. Or from source
First, you need to make a docker image. 

 - create the docker image: `sudo docker build -t enet2mqtt .`

Now that you have the docker image, you can create the docker container (replace variables with correct information):

    sudo docker run -d -e enet_user=[ENET_USER] -e enet_pass=[ENET_PASSWORD] -e mqtt_user=[MQTT_USER] -e mqtt_pass=[MQTT_PASSWORD] -e enet_ip=[ENET_IP] -e mqtt_ip=[MQTT_BROKER_IP] -e mqtt_port=[MQTT_PORT] -e uri_scheme=[URI_SCHEME] -e verify_ssl_cert=[VERIFY_SSL_CERT] --name enet2mqtt enet2mqtt
 - [ENET_USER] = Your enet username
 - [ENET_PASSWORD] = Your enet password
 - [MQTT_USER] = your mqtt username of your broker
 - [MQTT_PASSWORD] = your mqtt password of your broker
 - [ENET_IP] = your enet server IP
 - [MQTT_BROKER_IP] = your mqtt broker IP
 - [MQTT_PORT] = your mqtt broker port
 - [URI_SCHEME] = http or https (defaults to http if not specified)
 - [VERIFY_SSL_CERT] = TRUE or FALSE if your enet server has an untrusted HTTPS certificate (defaults to TRUE if not specified)
 
That is it!

### 3. If you have Unraid
This also as app downloadable from the community store! 


## Support
You always can make an issue there. But also take a look here [https://community.home-assistant.io/t/home-assistant-control-google-assistant-devices/164931/41](https://community.home-assistant.io/t/home-assistant-control-google-assistant-devices/164931/41)!

## Roadmap
- Make a HACS plugin.
