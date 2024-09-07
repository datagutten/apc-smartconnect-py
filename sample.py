import sys
from pprint import pprint

from apc_smartconnect import APCSmartConnect

if len(sys.argv) < 3:
    print('Usage: sample.py [username] [password]')
    exit(1)

smart = APCSmartConnect()
smart.login(sys.argv[1], sys.argv[2])

gateways = smart.gateways()  # Fetch all gateways (UPSs)
for gateway in gateways['gateways']:
    pprint(smart.gateway_info(gateway['deviceId']))
