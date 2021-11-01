#!/usr/bin/env python

# This file is part of krakenex.
# Licensed under the Simplified BSD license. See `examples/LICENSE.txt`.

# Prints the account blance to standard output.

import krakenex
import json

k = krakenex.API()
k.load_key('kraken.key')


def update_nonce():
    fnonce = open(r"nonce.txt","r")
    nonce = int(fnonce.read())
    fnonce.close()

    fnonce = open(r"nonce.txt","w")
    fnonce.write(str(nonce+1))
    fnonce.close()

    k.nonce = nonce+1

    print("NONCE =",k.nonce)



def get_balance():
    data = {}
    data['nonce'] = k.nonce
    urlpath = '/' + k.apiversion + '/private/Balance'

    headers = {
        'API-Key'  : k.key,
        'API-Sign' : k._sign(data,urlpath)
    }

    url = k.uri + urlpath

    k.response = k.session.post(url, data = data, headers = headers, timeout = 1)
    print(k.response.status_code,"  ",k.response.json())





update_nonce()
get_balance()