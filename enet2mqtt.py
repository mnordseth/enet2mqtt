import paho.mqtt.client as mqtt
import enet
import json
import time
import logging
import argparse

log = logging.getLogger(__name__)

class MqttEnetLight(enet.Channel):
    def get_ha_mqtt_config(self):
        location = self._device.location.replace("My home:", "")
        name=f"{location}:{self.name}"

        config = dict(name=name,
                      unique_id=self.uid,
                      brightness=self.has_brightness,
                      schema="json",
                      device={"name":f"{location}:{self._device.name}",
                              "identifiers":[self._device.uid],
                              "model":self._device.device_type,
                              "manufacturer":"Jung",
                          },
                      platform="mqtt",
                      brightness_scale=100,
                      command_topic=f"enet/{self.uid}/set",
                      state_topic=f"enet/{self.uid}/state")
        return json.dumps(config)

    def handle_mqtt_set(self, cmd):
        brightness = cmd.get("brightness")
        state = cmd.get("state")
        log.debug(f"cmd=cmd brightness={brightness} state={state}")
        if state == "ON":
            if brightness is not None:
                self.set_value(brightness)
            else:
                self.turn_on()
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

enet.Channel = MqttEnetLight

class Enet2MqttBridge(mqtt.Client):
    def __init__(self, enet_client, mqtt_host, mqtt_port, mqtt_user, mqtt_passwd):
        super().__init__()
        self.enet = enet_client
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_user = mqtt_user
        self.mqtt_passwd = mqtt_passwd
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

        self.devices = []
        for device in enet_devices:
            for channel in device.channels:
                self.devices.append(channel)
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
            self.publish(f"enet/{device_uid}/state", state, retain=True)
        else:
            log.warning(f"on_message: Unknown command '{command}'")

    def on_publish(self, mqttc, obj, mid):
        pass

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        log.debug(f"Subscribed: {mid} {granted_qos}")

    def on_log(self, mqttc, obj, level, string):
        pass

    def run(self):
        self.username_pw_set(self.mqtt_user, self.mqtt_passwd)
        self.connect(self.mqtt_host, self.mqtt_port, 60)
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
                topic = f"enet/{device.uid}/state"
                
                if published_state.get(topic) != state:
                    self.publish(topic, state, retain=True)
                    published_state[topic] = state
            time.sleep(self.enet_poll_interval)


def parseargs():
    parser = argparse.ArgumentParser(description='Publish Enet Smart Home devices to MQTT')
    parser.add_argument('enet_host', help='Enet server address')
    parser.add_argument('--enet_user', default="admin")
    parser.add_argument('--enet_passwd', default="admin")
    parser.add_argument('mqtt_host', help='MQTT Server address')
    parser.add_argument('--mqtt_port', type=int, default=1883)
    parser.add_argument('--mqtt_user', default="")
    parser.add_argument('--mqtt_passwd', default="")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parseargs()
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    
    enet_client = enet.EnetClient(args.enet_user, args.enet_passwd, args.enet_host)
    bridge = Enet2MqttBridge(enet_client, args.mqtt_host, args.mqtt_port, args.mqtt_user, args.mqtt_passwd)
    rc = bridge.run()
