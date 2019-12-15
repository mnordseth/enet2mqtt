import paho.mqtt.subscribe as subscribe
import enet
import json


def loop(devices):
    topic_device_map = {"enet/{}/set".format(device.uid):device for device in devices}
    topics = [(topic, 1) for topic in topic_device_map.keys()]
    print(topics)
    while True:
        print("Subscribing...")

        msg = subscribe.simple(topics, hostname="192.168.1.111")
        print("%s %s" % (msg.topic, msg.payload))
        device = topic_device_map.get(msg.topic)
        msg = json.loads(msg.payload)
        if "brightness" in msg:
            device.set_value(msg["brightness"])
        elif "state" in msg and msg["state"] == "OFF":
            device.turn_off()
            

def print_yaml(devices):
    values = []
    template = """  - platform: mqtt
    schema: json
    command_topic: "enet/%s/set"
    state_topic: "enet/%s/state"
    name: %s:%s
    brightness: true
    brightness_scale: 100"""
    for device in devices:
        if device.__class__.__name__ == "Light":
            values.append((template % (device.uid, device.uid, device.location,  device.name)))
    return values
        


if __name__ == "__main__":
    e = enet.EnetClient(enet.user, enet.passwd, enet.host)
    e.get_account()
    e.simple_login()
    e.get_account()
    devices = e.get_devices()
    loop(devices)
