import os
import tempfile

from apc_smartconnect import APCSmartConnect

cookies_temp = tempfile.NamedTemporaryFile()
apc = APCSmartConnect()
apc.login(os.getenv('APC_USER'), os.getenv('APC_PASS'))


def test_gateways():
    gateways = apc.gateways()
    assert type(gateways['gateways']) == list
    assert type(gateways['gateways'][0]['deviceId']) == str
