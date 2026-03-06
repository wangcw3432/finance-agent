import ssl
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

old_request = requests.Session.request
def new_request(*args, **kwargs):
    kwargs['verify'] = False
    return old_request(*args, **kwargs)
requests.Session.request = new_request

import akshare as ak
print([x for x in dir(ak) if 'us' in x.lower() and 'hist' in x.lower()])
print([x for x in dir(ak) if 'us' in x.lower() and 'daily' in x.lower()])
