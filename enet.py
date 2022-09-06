#!/usr/bin/env python

import requests
import hashlib
import pprint
import string
import random
import json
import logging

log = logging.getLogger(__name__)

session = requests.Session()
URL_MANAGEMENT="/jsonrpc/management"
URL_VIZ="/jsonrpc/visualization"
URL_COM="/jsonrpc/commissioning"
URL_TELEGRAM=URL_COM+"/app_telegrams"
URL_SCENE="/jsonrpc/visualization/app_scene"

class AuthError(Exception):
    pass


class EnetClient:
    def __init__(self, user, passwd, hostname, urischeme="http", sslverify="TRUE"):
        self.user = user
        self.passwd = passwd
        self.hostname = hostname
        self.urischeme = urischeme
        self._session = requests.Session()
        self._session.verify = sslverify.upper() == "TRUE"
        self._debug_requests = False
        self._api_counter = 1
        self._cookie=""
        self._last_telegram_ts={}
        self.devices = []


    def auth_if_needed(func):
        def auth_wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except AuthError:
                log.info("Trying to re-authenticate...")
                self.simple_login()

            return func(self, *args, **kwargs)
        return auth_wrapper


    @auth_if_needed
    def request(self, url, method, params=None, get_raw=False):
        
        req = {"jsonrpc":"2.0",
               "method":method,
               "params":params,
               "id":str(self._api_counter)
        }
        self._api_counter += 1
        response = self._session.post("%s://%s%s" % (self.urischeme, self.hostname, url), json=req)
        if get_raw:
            return response
        if response.status_code >= 400:
            log.warning(f"Request to {response.request.url} failed with status {response.status_code}")
            return response
        log=dict(request=dict(url=response.request.url,
                              headers=dict(response.request.headers),
                              body=req),
                response=dict(headers=dict(response.headers),
                              body=response.json()))
        self._cookie=log["response"]["headers"].get("X-ClientCredentials-SessionId")

        if self._debug_requests:
            pprint.pprint(log)
        if False:
            print(log["request"]["headers"].get("Cookie"))
            print(log["response"]["headers"].get("X-ClientCredentials-SessionId"))
        json = response.json()
        if "error" in json:
            e = "-> %s %s returned error: %s" %(url, method, json["error"])
            print(json["error"])
            if json["error"]["code"] == -29998:
                raise(AuthError)
            else:
                raise(Exception(e))
        else:
            if self._debug_requests:
                print("-> %s %s returned: %s" % (url, method, json["result"]))
        return json["result"]

  
    def simple_login(self):
        params = dict(userName=self.user,
                      userPassword=self.passwd)
        r = self.request(URL_MANAGEMENT, "userLogin", params)
        r = self.request(URL_MANAGEMENT, "setClientRole", dict(clientRole="CR_VISU"))
        

    def get_links(self, deviceUIDs=[]):
        r = self.request(URL_MANAGEMENT, "setClientRole", dict(clientRole="CR_IBN"))
        
        #devices = self.request(URL_VIZ, "getDeviceUIDs")
        #deviceUIDs = [i["deviceUID"] for i in devices["deviceUIDs"]]
        params={"deviceUIDs":deviceUIDs}
        result = self.request(URL_COM, "getLinksFromDevices", params)
        return result
        

    def request_events(self):
        return self.request(URL_VIZ, "requestEvents")
    
    def get_account(self):
        return self.request(URL_MANAGEMENT, "getAccount")

    def get_event_id(self, devUID=["83ec3031-f8f0-4972-a92b-2df300000213"]):
        if type(devUID) is not type([]):
            devUID=[devUID]
        params={"deviceUIDs":devUID,
                  "filter":".+\\\\.(SCV1|SCV2|SNA|PSN)\\\\[(.|1.|2.|3.)\\\\]+"}
        return self.request(URL_VIZ, "getDevicesWithParameterFilter", params)
    
    def get_current_values(self, output_device_uid):
        {"jsonrpc":"2.0", "method":"getCurrentValuesFromOutputDeviceFunction", "params":{"deviceFunctionUID":"83ec3031-f8f0-4972-a92b-2df300000c70"}, "id":"83"}
        params = {"deviceFunctionUID":output_device_uid}
        return self.request(URL_VIZ, "getCurrentValuesFromOutputDeviceFunction", params)
                                                                                         

    def get_devices_and_links(self):
        devices = self.request(URL_VIZ, "getDeviceUIDs")
        deviceUIDs = [i["deviceUID"] for i in devices["deviceUIDs"]]
        params={"deviceUIDs":deviceUIDs,
                  "filter":".+\\\\.(SCV1|SCV2|SNA|PSN)\\\\[(.|1.|2.|3.)\\\\]+"}
        result = self.request(URL_VIZ, "getDevicesWithParameterFilter", params)
        devices = result["devices"]

        links = self.get_links(deviceUIDs)
        links_by_devuid = dict([(l["uid"], l) for l in links["devices"]])
        for device in devices:
            device.update(links_by_devuid[device["uid"]])
          
    def get_devices(self):
        device_locations = self.get_device_locations()
        deviceUIDs = list(device_locations.keys())
        params={"deviceUIDs":deviceUIDs,
                  "filter":".+\\\\.(SCV1|SCV2|SNA|PSN)\\\\[(.|1.|2.|3.)\\\\]+"}
        result = self.request(URL_VIZ, "getDevicesWithParameterFilter", params)
        devices = result["devices"]
        devices = [Device(self, dev) for dev in devices if dev]
        for device in devices:
            device.location = device_locations[device.uid]
        return devices

    def set_value(self, device_function_uid, value):
        params = {"deviceFunctionUID":device_function_uid,
                  "values":[{"valueTypeID":"VT_SCALING_RANGE_0_100_DEF_0",
                             "value":value}]
        }
        result = self.request(URL_VIZ, "callInputDeviceFunction", params)
        log.debug(f"set_value(): {result}")

    def get_locations(self):
        params = {"locationUIDs":[]}
        result = self.request(URL_VIZ, "getLocations", params)        
        return result["locations"]

    def get_events(self):
        result = self.request(URL_VIZ, "requestEvents")
        log.debug("get_events(): " +  result)
    
    def foo(self):
        self.request(URL_VIZ, "getMigratingProjectUID")
        self.request(URL_COM, "isUpdateProcessActive")
        self.request(URL_VIZ, "getDeviceCatalogueManufacturerIDs")
        self.request(URL_VIZ, "getCurrentConfiguration")
        self.request(URL_VIZ, "getMetaDataFromDeviceCatalogue", params={"manufacturerID":"142"})
        self.request(URL_VIZ, "getDeviceCatalogueManufacturerIDs")

    def get_device_locations(self):
        locations = self.get_locations()
        device_to_loc = {}
        def recurse_locations(locations, parent=[], level=0):
            for location in locations:
                name = location["name"]
                #print(":".join(parent), name, level)
                hier_name = ":".join(parent) + ":" + name
                for device in location["deviceUIDs"]:
                    #print("  ", device)
                    device_to_loc[device["deviceUID"]] = hier_name
                if location["childLocations"]:
                    parent.append(name)
                    recurse_locations(location["childLocations"], parent, level+1)
            if parent:
                parent.pop()
        recurse_locations(locations)
        return device_to_loc




                
known_actuators = ["DVT_DA1M",  # Jung 1 channel dimming actuator
                   "DVT_SV1M",  # Jung 1 channel 1-10V dimming actuator
                   "DVT_DA4R",  # 4 channel dimming actuator rail mount
                   "DVT_DA1R",  # 1 channel dimming actuator rail mount
                   "DVT_SJAR",  # 8 channel switch actuator
                   "DVT_SA2M"   # Gira 2-gang switching actuator https://katalog.gira.de/en/datenblatt.html?id=635918

                   ]

known_sensors = ['DVT_TADO',
                 'DVT_WS2BJF50',
                 'DVT_WS2BJF50CL',
                 'DVT_WS3BJF50',
                 'DVT_WS4BJF50',
                 'DVT_US2M',
                 'DVT_WS1BG',
                 'DVT_SA1M',
                 'DVT_WS3BG',
                 'DVT_RPZS',
                 'DVT_SJA1',
                 'DVT_S2A1',
                 'DVT_HS2',
                 'DVT_HS4',
                 'DVT_WS3BJF50CL', 
                 'DVT_WS4BJF50CL', #
                 'DVT_BS1BP', # eNet motion detector
                 'DVT_SF1S',  # eNet light sensor
                 'DVT_WS4BJ'] # eNet radio transmitter module 4-gang


def Device(client, raw):
    device_type = raw["typeID"]
    if device_type in known_actuators:
        print("Actuator added: " + raw["typeID"])
        return Light(client, raw)
    elif device_type in known_sensors:
        print("Sensor added: " + raw["typeID"])
        return Switch(client, raw)
    else:
        log.warning(f'Unknown device: typeID={raw["typeID"]} name={raw["installationArea"]}')


class BaseEnetDevice:
    def __init__(self, client, raw):
        self.client = client
        self._raw = raw
        self.channels = []
        self.uid = self._raw["uid"]
        self.name = self._raw["installationArea"]
        self.device_type = self._raw["typeID"]
        self.battery_state = self._raw["batteryState"]
        self.software_update_available = self._raw["isSoftwareUpdateAvailable"]
    def __repr__(self):
        return "{}(Name: {} Type: {})".format(self.__class__.__name__, self.name, self.device_type)


class Switch(BaseEnetDevice):
    pass

class Light(BaseEnetDevice):
    def __init__(self, client, raw):
        super().__init__(client, raw)
        self.create_channels()
        
    def create_channels(self):
        print(f"Enet Device {self.name} type {self.device_type} has the following channels:")
        for ccg, channel_config_group in enumerate(self._raw['deviceChannelConfigurationGroups']):
            for dc, device_channel in enumerate(channel_config_group["deviceChannels"]):
                print(f"  ccg: {ccg} dc: {dc} Channel type: {device_channel['channelTypeID']} area: {device_channel['effectArea']}")
                if device_channel["channelTypeID"] != "CT_DEVICE":
                    c = Channel(self, device_channel)
                    self.channels.append(c)

                for odf, output_func in enumerate(device_channel["outputDeviceFunctions"]):
                    type_id = output_func['currentValues'][0]['valueTypeID']
                    value = output_func['currentValues'][0]['value']
                    print(f"    odf: {odf} type: {type_id} value: {value}")

    def __repr__(self):
        return "{}(Name: {} Type: {})".format(self.__class__.__name__, self.name, self.device_type)



class Channel:
    def __init__(self, device, raw_channel): #config_group_index = 1, channel_index=0, output_device_function=1):
        self._device = device
        self.channel = raw_channel
        self.uid = f"{self._device.uid}-{self.channel['no']}"
        self.channel_type = self.channel["channelTypeID"]
        self._output_device_function = 1
        self._input_device_function = 2
        self.name = self.channel["effectArea"]
        self.has_brightness=False
        self._iterate_output_functions()


    def _iterate_output_functions(self):
        for odf, output_func in enumerate(self.channel["outputDeviceFunctions"]):
            type_id = output_func['currentValues'][0]['valueTypeID']
            value = output_func['currentValues'][0]['value']
            print(f"    odf: {odf} type: {type_id} value: {value}")
            if type_id == "VT_SCALING_RANGE_0_100_DEF_0":
                self.has_brightness = True

    def _iterate_input_functions(self):
        for idf, input_func in enumerate(self.channel["inputDeviceFunctions"]):
            type_id = input_func['currentValues'][0]['valueTypeID']
            print(f"    idf: {idf} type: {type_id}")
            if type_id == "VT_SCALING_RANGE_0_100_DEF_0":
                self.has_brightness = True

    def get_value(self):
        output_function = self.channel['outputDeviceFunctions'][self._output_device_function]["uid"]
        current_value = self._device.client.get_current_values(output_function)
        value = current_value["currentValues"][0]["value"]
        log.debug(f"{self.name} get_value() returned {value}")
        self._last_value = value
        return value


    def set_value(self, value):
        input_function = self.channel['inputDeviceFunctions'][self._input_device_function]["uid"]
        log.info(f"{self.name} set_value({value})")
        self._device.client.set_value(input_function, value)

    def turn_off(self):
        params = {"deviceFunctionUID":self.channel["inputDeviceFunctions"][0]["uid"],
                  "values":[{"valueTypeID":"VT_SWITCH",
                             "value":False}]}
        result = self._device.client.request(URL_VIZ, "callInputDeviceFunction", params)
        log.info(f"{self.name} turn_off()")
        return result

    def turn_on(self):
        params = {"deviceFunctionUID":self.channel["inputDeviceFunctions"][0]["uid"],
                  "values":[{"valueTypeID":"VT_SWITCH",
                             "value":True}]}
        result = self._device.client.request(URL_VIZ, "callInputDeviceFunction", params)
        log.info(f"{self.name} turn_off()")
        return result

    def __repr__(self):
        return "{}(Name: {} Type: {} Value: {})".format(self.__class__.__name__, self.name, self.channel_type, self.get_value())
        

#import enet2mqtt

# SCENES
# IBOX
# {"jsonrpc":"2.0", "method":"getInputDeviceFunctionsFromDevice", "params":{"deviceUID":"83ec3031-f8f0-4972-a92b-2df300000001", "channelNumber":0}, "id":"47"}
# {"jsonrpc":"2.0","result":{"inputDeviceFunctions":[{"uid":"83ec3031-f8f0-4972-a92b-2df300000005","typeID":"IBOX_INScS.SSGI","active":true,"deviceFunctionDependency":null}]},"id":"47"}

# {"jsonrpc":"2.0", "method":"getOutputDeviceFunctionsFromDevice", "params":{"deviceUID":"83ec3031-f8f0-4972-a92b-2df300000001", "channelNumber":0}, "id":"50"}
# {"jsonrpc":"2.0","result":{"outputDeviceFunctions":[{"uid":"83ec3031-f8f0-4972-a92b-2df300000008","typeID":"IBOX_INScS.SC","active":true,"currentValues":[{"value":0,"valueTypeID":"VT_SCENE_NUMBER","valueUID":"83ec3031-f8f0-4972-a92b-2df300000006"},{"value":"ACTIVATE","valueTypeID":"VT_IN_SCENE_CONTROL","valueUID":"83ec3031-f8f0-4972-a92b-2df300000007"}],"deviceFunctionDependency":null},{"uid":"83ec3031-f8f0-4972-a92b-2df300000011","typeID":"IBOX_INScS.SSGET","active":true,"currentValues":[{"value":0,"valueTypeID":"VT_SSGET_CONNECTION_CODE","valueUID":"83ec3031-f8f0-4972-a92b-2df300000009"},{"value":0,"valueTypeID":"VT_SSGET_SEQUENCE_NUMBER","valueUID":"83ec3031-f8f0-4972-a92b-2df30000000a"},{"value":0,"valueTypeID":"VT_SSGET_COMMAND","valueUID":"83ec3031-f8f0-4972-a92b-2df30000000b"},{"value":0,"valueTypeID":"VT_SSGET_GROUP_ADDRESS","valueUID":"83ec3031-f8f0-4972-a92b-2df30000000c"},{"value":0,"valueTypeID":"VT_SSGET_SERIAL_NUMBER","valueUID":"83ec3031-f8f0-4972-a92b-2df30000000d"},{"value":"SUMSTATUS_GET","valueTypeID":"VT_SSGET_REQUEST_TYPE","valueUID":"83ec3031-f8f0-4972-a92b-2df30000000e"},{"value":false,"valueTypeID":"VT_SSGET_NO_COMMAND_FLAG","valueUID":"83ec3031-f8f0-4972-a92b-2df30000000f"},{"value":false,"valueTypeID":"VT_SSGET_REPEAT_FLAG","valueUID":"83ec3031-f8f0-4972-a92b-2df300000010"}],"deviceFunctionDependency":null}]},"id":"50"}

params = {"deviceFunctionUID":"83ec3031-f8f0-4972-a92b-2df300000005",
                  "values":[{"valueTypeID":"VT_SCENE_NUMBER",
                             "value":0}]}

