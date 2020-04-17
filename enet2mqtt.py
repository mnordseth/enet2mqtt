import paho.mqtt.client as mqtt
import enet
import json
import time
import logging

log = logging.getLogger(__name__)

mqtt_host = "10.0.0.3"
mqtt_port = 1883
mqtt_user = ""
mqtt_passwd = ""

enet_host = "10.0.0.102"
enet_user = "admin"
enet_passwd = "admin"

class MqttEnetLight(enet.Light):
    def get_ha_mqtt_config(self):
        name="{}:{}".format(self.location.replace("My home:", ""), self.name)

        config = dict(name=name,
                      unique_id=self.uid,
                      brightness=True,
                      schema="json",
                      device={"name":name,
                              "identifiers":[self.uid],
                              "model":self.device_type,
                              "manufacturer":"Jung",
                          },
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
        enet_devices = self.enet.get_devices()
        # Dump raw devices to file
        with open("devices.json", "w") as fp:
            json.dump([d._raw for d in enet_devices], fp, indent=2)
            print("Dumped all device info to devices.json")
        self.devices = [d for d in enet_devices if type(d) is MqttEnetLight]
        self.device_map = {device.uid:device for device in self.devices}

    def on_connect(self, mqttc, obj, flags, rc):
        log.debug("Connected: rc: {rc}")

    def on_message(self, mqttc, obj, msg):
        log.info(f"On message: {msg.topic} {msg.payload}")

        prefix, device_uid, command = msg.topic.split("/")
        if command == "set":
            device = self.device_map.get(device_uid)
            if not device:
                print("Unknown device uid: ", device_uid)
                return
            payload = json.loads(msg.payload.decode("utf-8"))
            state = device.handle_mqtt_set(payload)
            self.publish("enet/{}/state".format(device_uid), state, retain=True)
        else:
            log.warning(f"on_message: Unknown command '{command}'")

    def on_publish(self, mqttc, obj, mid):
        pass

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        log.debug(f"Subscribed: {mid} {granted_qos}")

    def on_log(self, mqttc, obj, level, string):
        pass

    def run(self):
        self.username_pw_set(mqtt_user, mqtt_passwd)
        self.connect(mqtt_host, mqtt_port, 60)
        self.subscribe("enet/+/set", 0)

        self.loop_start()
        self.ha_autodiscover()
        self.poll_enet()
        
    def ha_autodiscover(self):
        for device in self.device_map.values():
            config = device.get_ha_mqtt_config()
            topic = "{}/light/{}/config".format("homeassistant", device.uid)
            log.debug(f"HA Autoconfigure: {topic} {config}")
            self.publish(topic, config, retain=True)
            
            #self.publish(topic, "")

    def poll_enet(self):
        published_state = {}
        while True:
            log.debug("Polling enet devices...")
            for device in self.device_map.values():
                try:
                    state = device.get_mqtt_state()
                except:
                    log.exception("Failed to fetch status from enet:")
                    time.sleep(self.enet_poll_interval)
                    continue
                topic = "enet/{}/state".format(device.uid)
                
                if published_state.get(topic) != state:
                    self.publish(topic, state, retain=True)
                    published_state[topic] = state
            time.sleep(self.enet_poll_interval)

if __name__ == "__main__":
    
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    
    enet_client = enet.EnetClient(enet_user, enet_passwd, enet_host)
    bridge = Enet2MqttBridge(enet_client)
    rc = bridge.run()
