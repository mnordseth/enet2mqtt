# Enet2mqtt

Python library for communicating with the Gira / Jung eNet Smart Home Server (https://www.enet-smarthome.com/), and a mqtt forwarder to integrate eNet Smart Home devices with Home Assistant.



## Installation
First, you need to make a docker image. 
- Enter the correct information in the `start.sh`.
- Then create the docker image: `sudo docker build -t enet2mqtt-slim .`

Now that you have the docker image, you can create the docker container

    sudo docker run -d -p 1883:1883 --name enet2mqtt enet2mqtt-slim

We need to connect HA to our bridge.
- Go to `Devices & Services`
- `Add integration`
- `MQTT`
- Now enter your IP from the server where you are hosting the docker container. And enter as port `1883`.

That is it!



## Support
You always can make an issue there. But also take a look here [https://community.home-assistant.io/t/home-assistant-control-google-assistant-devices/164931/41](https://community.home-assistant.io/t/home-assistant-control-google-assistant-devices/164931/41)!

## Roadmap
- Make a HACS plugin.
