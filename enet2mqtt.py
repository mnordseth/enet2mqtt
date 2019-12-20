import paho.mqtt.client as mqtt
import enet
import json

import time

class MqttEnetLight(enet.Light):
    def get_ha_mqtt_config(self):
        config = dict(name="{}:{}".format(self.location, self.name),
                     brightness=True,
                     schema="json",
                     platform="mqtt",
                     brightness_scale=100,
                     command_topic="enet/{}/set".format(self.uid),
                     state_topic="enet/{}/state".format(self.uid))
        return json.dumps(config)

    def handle_mqtt_set(self, cmd):

        brightness = cmd.get("brightness")
        state = cmd.get("state")
        if state == "ON":
            if brightness is not None:
                self.set_value(brightness)
            else:
                self.set_value(self._last_value)
        elif state == "OFF":
            self.turn_off()
            brightness = 0
        return self.get_mqtt_state(brightness)

    def get_mqtt_state(self, value=None):
        if value is None:
            value = self.get_value()
        state = dict(state="OFF" if value == 0 else "ON",
                     brightness=value)
        return json.dumps(state)

enet.Light = MqttEnetLight

class Enet2MqttBridge(mqtt.Client):
    def __init__(self, enet_client):
        super().__init__()
        self.enet = enet_client
        self.device_map = {}
        self.enet_connect()
        self.enet_poll_interval = 30

    def enet_connect(self):
        self.enet.get_account()
        self.enet.simple_login()
        self.enet.get_account()
        self.devices = [d for d in self.enet.get_devices() if type(d) is MqttEnetLight]
        self.device_map = {device.uid:device for device in self.devices}

    def on_connect(self, mqttc, obj, flags, rc):
        print("rc: "+str(rc))

    def on_message(self, mqttc, obj, msg):
        print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
        prefix, device_uid, command = msg.topic.split("/")
        if command == "set":
            device = self.device_map.get(device_uid)
            if not device:
                print("Unknown device uid: ", device_uid)
                return
            payload = json.loads(msg.payload)
            state = device.handle_mqtt_set(payload)
            self.publish("enet/{}/state".format(device_uid), state, retain=True)
        else:
            print("Unknown command")

    def on_publish(self, mqttc, obj, mid):
        pass
        #print("mid: "+str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        print("LOG: ", string)
        pass

    def run(self):
        self.connect("192.168.1.111", 1883, 60)
        self.subscribe("enet/+/set", 0)

        self.loop_start()
        self.ha_autodiscover()
        self.poll_enet()
        
    def ha_autodiscover(self):
        for device in self.device_map.values():
            config = device.get_ha_mqtt_config()
            topic = "{}/light/{}/config".format("homeassistant", device.uid)
            print("Autoconfigure: ", topic, config)
            self.publish(topic, config)

    def poll_enet(self):
        published_state = {}
        while True:
            print("Polling enet devices...")
            for device in self.device_map.values():
                state = device.get_mqtt_state()
                topic = "enet/{}/state".format(device.uid)
                
                if published_state.get(topic) != state:
                    self.publish(topic, state, retain=True)
                    published_state[topic] = state
            time.sleep(self.enet_poll_interval)

if __name__ == "__main__":
    enet_client = enet.EnetClient(enet.user, enet.passwd, enet.host)

    bridge = Enet2MqttBridge(enet_client)
    rc = bridge.run()
    #print("rc: "+str(rc))