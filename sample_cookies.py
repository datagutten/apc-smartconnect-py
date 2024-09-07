import os.path
import sys
from pprint import pprint
import requests

from apc_smartconnect import APCSmartConnect

if len(sys.argv) < 3:
    print('Usage: sample_cookies.py [username] [password]')
    exit(1)

smart = APCSmartConnect()
if os.path.exists('apc_cookies.json'):
    smart.load_cookies('apc_cookies.json')

try:
    gateways = smart.gateways()  # Fetch all gateways (UPSs)
except requests.HTTPError as e:
    if e.response.status_code == 401:
        smart.login(sys.argv[1], sys.argv[2])
    else:
        raise e

    gateways = smart.gateways()  # Fetch all gateways (UPSs)

for gateway in gateways['gateways']:
    pprint(smart.gateway_info(gateway['deviceId']))
