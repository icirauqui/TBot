import socket
import ssl
import json

keyid1 = 'api-key-1618670890550'
key1 = 'iKXSsmpbr6wL5tcU67gu2mqv2ncBxgHDSBaDYeGecr/IZRK2XbGZqS8I'
pkey1 = '5xTNpK/YYr6CyV6IkoPG2BoNNHzK9D1IACNn5GWdA7atTNGYJPE8SV7bnZU7ZQ0GZMQVQesYVxXyZSoRPEbIyA=='

class API(object):
    def __init__(self, key='', secret=''):
        self.key = key
        self.secret = secret
        self.uri = 'https://api.kraken.com'
        self.apiversion = '0'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'krakenex/' + version.__version__ + ' (+' + version.__url__ + ')'
        })
        self.response = None
        self._json_options = {}


k = API(key=key1,secret=pkey1)



url = 'https://api.kraken.com/0/private/Balance'
api_host = 'https://api.kraken.com'

s = socket.socket()
s.connect((api_host,))
