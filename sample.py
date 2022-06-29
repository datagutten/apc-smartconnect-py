import sys
from pprint import pprint

import requests

from apc_smartconnect import APCSmartConnect

smart = APCSmartConnect()

# Try to query using saved cookies
try:
    gateways = smart.gateways()
except requests.exceptions.HTTPError as e:
    if len(sys.argv) < 3:
        print('Usage: sample.py [username] [password]')
        exit(1)

    smart.login(sys.argv[1], sys.argv[2])
    gateways = smart.gateways()

for gateway in gateways:
    pprint(smart.gateway_info(gateway))
