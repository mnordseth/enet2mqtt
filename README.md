
# Enet2mqtt
Python library for communicating with the Gira / Jung eNet Smart Home Server (https://www.enet-smarthome.com/), and a mqtt forwarder to integrate eNet Smart Home devices with Home Assistant.


## Installation
First, you need to make a docker image. 
- Enter the correct information in the `start.sh`.
	- `./usr/local/bin/python3.7 enet2mqtt.py --enet_user [ENTER USERNAME] --enet_passwd [ENTER PASSWORD]  [IP ENET SERVER] 127.0.0.1`
	[ENTER USERNAME] = the username to log in to the Enet app.
	[ENTER PASSWORD] = the password to log in to the Enet app.
	[IP ENET SERVER] = the IP from the Enet server. You can find it in the Enet app, in the menu `Connected with  xxx.xxx.xx.xx` and here is xxx.xxx.xx.xx the IP
	Example: `./usr/local/bin/python3.7 enet2mqtt.py --enet_user admin --enet_passwd password01 192.168.1.32 127.0.0.1`
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
