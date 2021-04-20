import sys

import krakenex
import json
import time

import pandas as pd

from tbot6_mysql import *

api_delay = 1




def api_update_nonce():
    fnonce = open(r"nonce.txt","r")
    nonce = int(fnonce.read())
    fnonce.close()

    fnonce = open(r"nonce.txt","w")
    fnonce.write(str(nonce+1))
    fnonce.close()

    k.nonce = nonce+1
    print("NONCE =",k.nonce)
    time.sleep(api_delay)




def api_get_balance():
    data = {}
    data['nonce'] = k.nonce
    urlpath = '/' + k.apiversion + '/private/Balance'
    url = k.uri + urlpath

    headers = {
        'API-Key'  : k.key,
        'API-Sign' : k._sign(data,urlpath)
    }
    
    api_update_nonce()
    try:
        k.response = k.session.post(url, data = data, headers = headers, timeout = 1)
        ret = k.response.json()
        if not 'result' in ret:
            ret['result'] = {'ZEUR':'0.0000'}
    except:
        ret = {'ZEUR':'0.0000'}

    save_balance(ret['result'])
    return ret['result']['ZEUR']


def get_balance():
    with open('balance.json','r') as f:
        try:
            return json.load(f)
        except:
            return api_get_balance()


def save_balance(data):
    with open('balance.json','w') as f:
        json.dump(data,f,indent=4)


def update_balance(amount,name,price,sold):
    balance = get_balance()
    if sold:
        balance.pop(name[:-4],None)
        balance['ZEUR'] = str(float(balance['ZEUR']) + amount*price)
    else:
        balance['ZEUR'] = str(float(balance['ZEUR']) - amount*price)
        balance[name[:-4]] = str(amount)
    save_balance(balance)
    return balance




def api_get_ticker(asset=''):
    urlpath = '/' + k.apiversion + '/public/Ticker'
    url = k.uri + urlpath

    data = {}
    data['nonce'] = k.nonce

    pairlist = ''
    if (asset==''):
        for pair in pairs:
            pairlist = pairlist  + pair[1:len(pair)-4] + "EUR" + ','
        pairlist = pairlist[:-1]
    else:
        pairlist = asset[1:len(asset)-4] + "EUR"
    data['pair'] = pairlist

    headers = {
        'API-Key'  : k.key,
        'API-Sign' : k._sign(data,urlpath)
    }

    api_update_nonce()
    try:
        k.response = k.session.post(url, data = data, headers = headers, timeout = 2)
        resp = k.response.json()['result']
        for pair in pairs:
            pair1 = pair[1:len(pair)-4] + 'EUR'
            if pair1 in resp:
                resp[pair] = resp.pop(pair1)
        return resp
    except:
        if (asset==''):
            resp = {}
            for pair in pairs:
                resp.update({pair: [[0, '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', 31]], 'last': 0})
            return resp
        else:
            resp = {asset: [[0, '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', 31]], 'last': 0}
            return resp


def api_get_ticker_ohlc(asset,since):
    urlpath = '/' + k.apiversion + '/public/OHLC'
    url = k.uri + urlpath

    data = {}
    data['nonce'] = k.nonce
    data['pair'] = asset[1:len(asset)-4] + "EUR"
    if since > '':
        data['since'] = since

    headers = {
        'API-Key'  : k.key,
        'API-Sign' : k._sign(data,urlpath)
    }

    api_update_nonce()
    try:
        k.response = k.session.post(url, data = data, headers = headers, timeout = 2)
        resp = k.response.json()['result']
        asset1 = asset[1:len(asset)-4] + 'EUR'
        resp[asset] = resp.pop(asset1)
        return resp
        #return k.response.json()['result'][asset]
    except:
        return {asset: [[0, '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', 31]], 'last': 0}


def get_purchasing_price(name):
    trades = load_trades()
    return trades[name][-1]['price_eur']


def api_get_trades(asset):
    data = {}
    data['nonce'] = k.nonce
    urlpath = '/' + k.apiversion + '/private/OpenOrders'
    url = k.uri + urlpath

    if asset > '':
        data['userref'] = asset

    headers = {
        'API-Key'  : k.key,
        'API-Sign' : k._sign(data,urlpath)
    }

    k.response = k.session.post(url, data = data, headers = headers, timeout = 1)
    print(k.response.status_code,"  ",k.response.json())

    api_update_nonce()
    return k.response.json()


def get_pairs():
    pairs = pd.read_csv('pairs.csv')
    pairsl = pairs['id'].to_list()
    return pairsl




# Load crypto data from files, i.e., last prices. If file empty, create json for all pairs
def load_crypto_data_from_file():
    data = {}
    with open('data.json','r') as f:
        try:
            data = json.load(f)
        except:
            data = make_crypto_data(data)
            save_crypto_data(data)
        return data


def make_crypto_data(data):
    for name in get_pairs():
        data[name] = {
            'high'  : [],
            'low'   : [],
            'close' : [],
            'prices': []
        }
    return data


def save_crypto_data(data):
    with open('data.json','w') as f:
        json.dump(data,f,indent=4)




def load_trades():
    trades = {}
    with open('trades.json','r') as f:
        try:
            trades = json.load(f)
        except:
            for crypto in pairs:
                trades[crypto] = []
    return trades




def bot(since, k, pairs):
    while True:
        for pair in pairs:
            trades = load_trades()
            
            crypto_data = api_get_ticker_ohlc(pair,since)
            print(crypto_data)
            if len(trades[pair]) > 0:
                if trades[pair][-1]['sold'] or trades[pair][-1]==None:
                    # Check if we should buy
                    check_data(pair,crypto_data,True)
                if trades[pair][-1]['bought']:
                    # Check if we should sell
                    check_data(pair,crypto_data,False)
            else:
                check_data(pair,crypto_data,True)
        time.sleep(20)


def check_data(name, crypto_data, should_buy):
    high = 0
    low = 0
    close = 0
    for b in crypto_data[-100:]:
        if b not in mva[name]['prices']:
            mva[name]['prices'].append(b)
        high += float(b[2])
        low += float(b[3])
        close += float(b[4])

    mva[name]['high'].append(high/100)
    mva[name]['low'].append(low/100)
    mva[name]['close'].append(close/100)

    save_crypto_data(mva)

    if should_buy:
        try_buy(mva[name],name,crypto_data)
    else:
        try_sell(mva[name],name,crypto_data)


def try_buy(data,name,crypto_data):
    # Analyse data to see if it is a good oportunity to buy
    make_trade = check_opportunity(data,name,False,True)
    if make_trade:
        buy_crypto(crypto_data,name)


def buy_crypto(crypto_data,name):
    # Execute trade
    analysis_data = clear_crypto_data(name)
    # Make sure to make the trade before the next line of code
    # Find what we can buy for
    price = float(crypto_data[-1][4])
    funds = get_available_funds()
    amount = funds * (1/price)
    balance = update_balance(amount,name,price,False)
    save_trade(price,name,True,False,amount)
    print('buy')

   
def try_sell(data,name,crypto_data):
    # Analyse data to see if it is a good oportunity to sell
    make_trade = check_opportunity(data,name,True,False)
    if make_trade:
        sell_crypto(crypto_data,name)


def sell_crypto(crypto_data,name):
    balance = api_get_balance()
    analysis_data = clear_crypto_data(name)
    price = float(crypto_data[-1][4])
    amount = float(balance[name[:-4]])
    balance = update_balance(amount,name,price,True)
    save_trade(price,name,False,True,amount)
    print('sell')


def clear_crypto_data(name):
    data = load_crypto_data_from_file()
    for key in data[name]:
        data[name][key] = delete_entries(data[name],key)
    save_crypto_data(data)
    return data


def delete_entries(data,key):
    clean_array = []
    for entry in data[key][-10:]:
        clean_array.append(entry)
    return clean_array


def check_opportunity(data,name,sell,buy):
    # calculate percentage increase of each point
    count = 0
    previous_value = 0
    trends = []
    for mva in data['close'][-10:]:
        if previous_value == 0:
            previous_value = mva
        else:
            if mva/previous_value>1:
                trends.append('UPTREND')
                if count < 1:
                    count = 1
                else:
                    count += 1
            elif mva/previous_value < 1:
                trends.append('DOWNTREND')
                if count > 0: 
                    count = -1
                else:
                    count -= 1
            else:
                trends.append('NOTREND')
            previous_value = mva
    
    areas = []
    for mva in reversed(data['close'][-5:]):
        area = 0
        price = float(data['prices'][-1][3])
        if sell:
            purchase_price = float(get_purchasing_price(name))
            if price >= (purchase_price * 1.02):
                print('Should sell with 10% profit')
                return True
            if price < purchase_price:
                print('Selling at a loss')
                return True
        areas.append(mva/price)

    if buy:
        counter = 0
        if count>=5:
            for area in areas:
                counter += area
            if counter/3 > 1.05:
                return True

    return False



if __name__ == '__main__':
    k = krakenex.API()
    k.load_key('kraken.key')
    api_update_nonce()
    pairs = get_pairs()
    since = str(int(time.time()-43200))
    mva = load_crypto_data_from_file()
    #bot(since,k,pairs)
