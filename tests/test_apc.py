import os
import tempfile

from apc_smartconnect import APCSmartConnect

cookies_temp = tempfile.NamedTemporaryFile()
apc = APCSmartConnect(os.path.join(tempfile.TemporaryDirectory().name, 'cookies.lwp'))
apc.login(os.getenv('APC_USER'), os.getenv('APC_PASS'))


def test_gateways():
    gateways = apc.gateways()
    assert type(gateways) == list
    assert type(gateways[0]) == str
