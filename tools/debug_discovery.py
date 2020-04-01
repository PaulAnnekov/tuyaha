# The script is intended to get a list of all devices available via Tuya Home Assistant API endpoint.
import requests
import pprint

# CHANGE THIS - BEGGINING
USERNAME = ""
PASSWORD = ""
REGION = "eu" # cn, eu, us
COUNTRY_CODE = "1" # Your account country code, e.g., 1 for USA or 86 for China
BIZ_TYPE = "smart_life" # tuya, smart_life, jinvoo_smart
FROM = "tuya" # you likely don't need to touch this
# CHANGE THIS - END

# NO NEED TO CHANGE ANYTHING BELOW
TUYACLOUDURL = "https://px1.tuya{}.com"

pp = pprint.PrettyPrinter(indent=4)

print("Getting credentials")
auth_response = requests.post(
    (TUYACLOUDURL + "/homeassistant/auth.do").format(REGION),
    data={
        "userName": USERNAME,
        "password": PASSWORD,
        "countryCode": COUNTRY_CODE,
        "bizType": BIZ_TYPE,
        "from": FROM,
    },
)
print("Got credentials")
auth_response = auth_response.json()
pp.pprint(auth_response)

header = {"name": "Discovery", "namespace": "discovery", "payloadVersion": 1}
payload = {"accessToken": auth_response["access_token"]}
data = {"header": header, "payload": payload}
print("Getting devices")
discovery_response = requests.post(
    (TUYACLOUDURL + "/homeassistant/skill").format(REGION), json=data
)
print("Got devices")
discovery_response = discovery_response.json()
pp.pprint(discovery_response)
print("!!! NOW REMOVE THIS FILE, SO YOUR CREDENTIALS (username, password) WON'T LEAK !!!")
