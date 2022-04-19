#!/bin/bash

./usr/sbin/mosquitto -d
./usr/local/bin/python3.7 enet2mqtt.py --enet_user [ENTER USERNAME] --enet_passwd [ENTER PASSWORD]  [IP ENET SERVER] 127.0.0.1
