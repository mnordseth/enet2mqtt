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
user = "admin"
passwd = "admin"
host = "192.168.1.115"

URL_MANAGEMENT="/jsonrpc/management"
URL_VIZ="/jsonrpc/visualization"
URL_COM="/jsonrpc/commissioning"

class EnetClient:
    def __init__(self, user, passwd, hostname):
        self.user = user
        self.passwd = passwd
        self.hostname = hostname
        self._session = requests.Session()
        self._debug_requests = False
        self._api_counter = 1
        self._cookie=""
        self.devices = []
        #self._cookie="1ahlme9ytcbm311qphlvofmmwz"

    def request(self, url, method, params=None):
        
        req = {"jsonrpc":"2.0",
               "method":method,
               "params":params,
               "id":str(self._api_counter)
        }
        self._api_counter += 1
        response = self._session.post("http://%s%s" % (self.hostname, url), json=req)
        #headers = {}
        #if self._cookie:
        #    headers["Cookie"] = "INSTASESSIONID=%s" % self._cookie
        #response = requests.post("http://%s%s" % (self.hostname, url), json=req, headers=headers)

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
            raise(Exception(e))
        else:
            if self._debug_requests:
                print("-> %s %s returned: %s" % (url, method, json["result"]))
        return json["result"]

    def _calc_auth_response(self, challenge, cnonce=None):
        if cnonce is None:
            cnonce= "".join(random.choice(string.ascii_letters + string.digits) for i in range(40))

        realm = challenge["realm"]
        nonce = challenge["nonce"]
        uri = challenge["uri"]

        ha1 = "{}:{}:{}".format(user, realm, passwd)
        ha1 = hashlib.sha1(ha1.encode()).hexdigest().upper()
        ha2 = hashlib.sha1(("POST:%s" % uri).encode()).hexdigest().upper()
        nc="00000001"

        
        response = "{}:{}:{}:{}:{}:{}".format(ha1, challenge["nonce"], nc, cnonce, "auth", ha2)
        response = hashlib.sha1(response.encode()).hexdigest().upper()

        params = {"userName":user,
                   "uri":uri, 
                   "qop":"auth",
                   "cnonce":cnonce,
                   "nc":"00000001",
                   "response":response,
                   "realm":realm,
                   "nonce":nonce,
                   "algorithm":"sha",
                   "opaque":challenge["opaque"]
        }
        return params
            

    def simple_login(self):
        params = dict(userName=self.user,
                      userPassword=self.passwd)
        r = self.request(URL_MANAGEMENT, "userLogin", params)
        r = self.request(URL_MANAGEMENT, "setClientRole", dict(clientRole="CR_VISU"))
        
    
    def login(self):
        challenge = self.request(URL_MANAGEMENT, "getDigestAuthentificationInfos").json()["result"]
        response = self._calc_auth_response(challenge)
        r = self.request(URL_MANAGEMENT, "userLoginDigest", response)

        # For some reason I don't get, this request has to be made for auth to work for following requests...
        r = self._session.get("http://%s/wslclient.html?icp=6p1C8GeIi2FOOEfeA85a" % self.hostname)


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
        devices = [Device(self, dev) for dev in devices]
        for device in devices:
            device.location = device_locations[device.uid]
        return devices

    def set_value(self, device_function_uid, value):
        params = {"deviceFunctionUID":device_function_uid,
                  "values":[{"valueTypeID":"VT_SCALING_RANGE_0_100_DEF_0",
                             "value":value}]
        }
        result = self.request(URL_VIZ, "callInputDeviceFunction", params)

    def set_device_name_value(self, device_name, value):
        # get device_function_uid from device
        dev_function_uid = dev_by_name[device_name]["deviceChannelConfigurationGroups"][1]["deviceChannels"][0]['inputDeviceFunctions'][2]["uid"]
        return self.set_value(dev_function_uid, value)
        
    def get_locations(self):
        params = {"locationUIDs":[]}
        result = self.request(URL_VIZ, "getLocations", params)        
        return result["locations"]

    def get_events(self):
        result = self.request(URL_VIZ, "requestEvents")
        log.debug("get_events(): ", result)
    
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

def Device(client, raw):
    device_type = raw["typeID"]
    if device_type in ["DVT_DA1M", "DVT_SV1M"]:
        return Light(client, raw)
    elif device_type in ['DVT_WS2BJF50CL', 'DVT_WS3BJF50', 'DVT_WS3BJF50CL', 'DVT_WS4BJF50CL']:
        return Switch(client, raw)
    else:
        log.warning(f'Unknown device: typeID={raw["typeID"]} name={raw["installationArea"]}')


class BaseEnetDevice:
    def __init__(self, client, raw):
        self.client = client
        self._raw = raw
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
    def get_value(self):
        output_function = self._raw['deviceChannelConfigurationGroups'][1][ 'deviceChannels'][0]['outputDeviceFunctions'][1]["uid"]
        current_value = self.client.get_current_values(output_function)
        value = current_value["currentValues"][0]["value"]
        log.debug(f"{self.name} get_value() returned {value}")
        self._last_value = value
        return value


    def set_value(self, value):
        input_function = self._raw["deviceChannelConfigurationGroups"][1]["deviceChannels"][0]['inputDeviceFunctions'][2]["uid"]
        log.info(f"{self.name} set_value({value})")
        self.client.set_value(input_function, value)

    def turn_off(self):
        return self.set_value(0)
    
    def turn_on(self):
        return self.set_value(100)

    def __repr__(self):
        return "{}(Name: {} Type: {} Value: {})".format(self.__class__.__name__, self.name, self.device_type, self.get_value())
        

if __name__ == "__main__":
    e = EnetClient(user, passwd, host)
    e.get_account()
    e.simple_login()
    e.get_account()
    devices = e.get_devices()
