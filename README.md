
# Enet2mqtt
Python library for communicating with the Gira / Jung eNet Smart Home Server (https://www.enet-smarthome.com/), and a mqtt forwarder to integrate eNet Smart Home devices with Home Assistant.


## Installation
### Requirements

 1. You have a mqtt broker. (Like mosquitto.)
 2. You have Home Assistant running.
 3. You know how to use docker.
 
### The installation 
First, you need to make a docker image. 

 - create the docker image: `sudo docker build -t enet2mqtt .`

Now that you have the docker image, you can create the docker container

    sudo docker run -d -e enet_user=[ENET_USER] -e enet_pass=[ENET_PASSWORD] -e mqtt_user=[MQTT_USER] -e mqtt_pass=[MQTT_PASSWORD] -e enet_ip=[ENET_IP] -e mqtt_ip=[MQTT_BROKER_IP] --name enet2mqtt enet2mqtt

 - [ENET_USER] = Your enet username
 - [ENET_PASSWORD] = Your enet password
 - [MQTT_USER] = your mqtt username of your broker
 - [MQTT_PASSWORD] = your mqtt password of your broker
 - [ENET_IP] = your enet server IP
 - [MQTT_BROKER_IP] = your mqtt broker IP

That is it!



## Support
You always can make an issue there. But also take a look here [https://community.home-assistant.io/t/home-assistant-control-google-assistant-devices/164931/41](https://community.home-assistant.io/t/home-assistant-control-google-assistant-devices/164931/41)!

## Roadmap
- Make a HACS plugin.
