import json
import re
from http.cookiejar import LWPCookieJar

import requests
import requests.utils


def get_salesforce_keys(page):
    patterns = {
        'com.salesforce.visualforce.ViewState': r'"com.salesforce.visualforce.ViewState"\s+value="([^"]+)"',
        'com.salesforce.visualforce.ViewStateVersion': r'"com.salesforce.visualforce.ViewStateVersion"\s+value="([^"]+)"',
        'com.salesforce.visualforce.ViewStateMAC': r'"com.salesforce.visualforce.ViewStateMAC"\s+value="([^"]+)"'
    }

    keys = {}
    for key, pattern in patterns.items():
        matches = re.search(pattern, page)
        if not matches:
            raise ValueError('Keys not found')
        keys[key] = matches.group(1)

    return keys


class APCSmartConnect:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'nb-NO,nb;q=0.9,no;q=0.8,nn;q=0.7,en-US;q=0.6,en;q=0.5,da;q=0.4,und;q=0.3',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'})
        requests.utils.add_dict_to_cookiejar(self.session.cookies, {'clientSrc': '23.48.94.21'})

    def load_cookies(self, file: str):
        """
        Load cookiejar from a json encoded dict
        """
        with open(file) as fp:
            requests.utils.add_dict_to_cookiejar(self.session.cookies, json.load(fp))

    def save_cookies(self, file: str):
        """
        Save cookiejar to a json encoded dict
        """
        cookies = requests.utils.dict_from_cookiejar(self.session.cookies)
        with open(file, 'w') as fp:
            json.dump(cookies, fp)

    def get_cookies(self, page):
        cookie = {}
        matches = re.finditer(r'document.cookie\s*=\s+"([^"]+)=([^"]+);Path=(.);(secure)?";',
                              page)
        for match in matches:
            cookie[match.group(1)] = match.group(2)

        requests.utils.add_dict_to_cookiejar(self.session.cookies, cookie)

    def get_redirect(self, page, prefix=None):
        return self.session.get(get_redirect_url(page, prefix))

    def get_meta_redirect(self, page):
        matches = re.search(r'<meta name="Location" content="(.+?)"', page)
        if not matches:
            if page.find('captcha.error') > -1:
                raise RuntimeError('Captcha required')
            else:
                raise RuntimeError('Unable to find redirect URL')
        url = matches.group(1)
        return self.session.get(url)

    def send_login(self, page, usrname, jid):
        data = {
            'AJAXREQUEST': '_viewRoot',
            jid[0]: jid[0]
        }
        data.update(get_salesforce_keys(page))
        data[jid[1]] = jid[1]
        data['usrname'] = usrname
        data[''] = ''
        url = 'https://secureidentity.schneider-electric.com/identity/UserLogin'

        return self.session.post(url, data)

    def login(self, username, password):
        response = self.session.get('https://smartconnect.apc.com/auth/login',
                                    allow_redirects=False)
        # self.session.cookies.update(response.cookies)
        if response.headers['Location'][0:4] != 'http':
            raise ValueError('Location header is not a valid URL')
        response = self.session.get(response.headers['Location'])
        self.get_cookies(response.text)

        # Get login page
        redirect_url = 'https://secureidentity.schneider-electric.com' + get_redirect_url(
            response.text)
        response = self.session.get(redirect_url)
        response.raise_for_status()
        jid_step1 = get_jid(response.text, 1)
        jid_step2 = get_jid(response.text, 2)

        response1 = self.send_login(response.text, username, jid_step1)
        response1.raise_for_status()
        response2 = self.send_login(response1.text, password, jid_step2)
        response2.raise_for_status()
        frontdoor = self.get_meta_redirect(response2.text)
        response_apex = self.get_redirect(frontdoor.text)
        response_setup = self.get_redirect(response_apex.text,
                                           'https://secureidentity.schneider-electric.com')
        response_check = self.get_redirect(response_setup.text)
        response_check.raise_for_status()

    def get(self, uri):
        response = self.session.get('https://smartconnect.apc.com/api/v1/' + uri)
        response.raise_for_status()
        return response.json()

    def gateways(self):
        return self.get('gateways')

    def gateway_info(self, gateway_id):
        return self.get(
            'gateways/%s' % gateway_id)

    def gateway_info_detail(self, gateway_id):
        return self.get(
            'gateways/%s?collection=input,output,battery,network,main_outlet,switched_outlets' % gateway_id)

    def documentation(self, sku):
        return self.get('documentation/ups/documents?sku=' + sku)


def get_redirect_url(page, prefix=None):
    matches = re.search(r'window.location\s*=\s+"([^"]+)";', page)
    if not matches:
        matches = re.search(r'window\.location(?:.[a-z]+)?\s*\([\x22\x27](.+)[\x22\x27]\);',
                            page)
    if prefix:
        url = prefix + matches.group(1)
    else:
        url = matches.group(1)

    return url


def get_jid(page, step):
    matches = re.search(
        r"dicvLogin%dAct.+?Submit\('(j_id0:j_id[0-9]+)'.+?similarityGroupingId':'(j_id0:j_id\d+:j_id\d+)'" % step,
        page)
    return matches.group(1), matches.group(2)
