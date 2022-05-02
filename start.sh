#!/bin/bash

./usr/local/bin/python3.7 enet2mqtt.py --enet_user ${enet_user} --enet_passwd ${enet_pass} --mqtt_user ${mqtt_user} --mqtt_passwd ${mqtt_pass} ${enet_ip} ${mqtt_ip}
