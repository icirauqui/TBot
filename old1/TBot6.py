import sys

import krakenex
import json
import time
import math
import datetime

import pandas as pd

api_delay = 1
cryptos_not_owned = 2

blive = True

sema = 1
lema = 2



def api_update_nonce():
    fnonce = open(r"nonce.txt","r")
    nonce = int(fnonce.read())
    fnonce.close()

    fnonce = open(r"nonce.txt","w")
    fnonce.write(str(nonce+1))
    fnonce.close()

    k.nonce = nonce+1
    #print("NONCE =",k.nonce)
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
    return ret['result']


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
        if name[4:] == 'ZEUR':
            balance.pop(name[:-4],None)
        else:
            balance.pop(name[:-3],None)
        balance['ZEUR'] = str(float(balance['ZEUR']) + amount*price)
    else:
        balance['ZEUR'] = str(float(balance['ZEUR']) - amount*price)
        if name[4:] == 'ZEUR':
            balance[name[:-4]] = str(amount)
        else:
            balance[name[:-3]] = str(amount)
    save_balance(balance)
    return balance


def get_available_funds():
    balance = get_balance()
    money = float(balance['ZEUR'])
    cryptos_not_owned = len(pairs) - (len(balance)-1)
    funds = money/cryptos_not_owned
    funds = rounddown(funds,8)
    return funds


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
    #data['pair'] = asset[1:len(asset)-4] + "EUR"
    data['pair'] = asset
    if since > '':
        data['since'] = since

    headers = {
        'API-Key'  : k.key,
        'API-Sign' : k._sign(data,urlpath)
    }

    api_update_nonce()
    #print(asset)
    try:
        k.response = k.session.post(url, data = data, headers = headers, timeout = 2)
        resp = k.response.json()['result']
        #asset1 = asset[1:len(asset)-4] + 'EUR'
        #resp[asset] = resp.pop(asset1)
        return resp[asset]
    except:
        return [[0, '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', 31]]


def api_get_ticker_ohlc_test(asset,since):
    urlpath = '/' + k.apiversion + '/public/OHLC'
    url = k.uri + urlpath

    data = {}
    data['nonce'] = k.nonce
    #data['pair'] = asset[1:len(asset)-4] + "EUR"
    data['pair'] = asset
    if since > '':
        data['since'] = since

    headers = {
        'API-Key'  : k.key,
        'API-Sign' : k._sign(data,urlpath)
    }

    api_update_nonce()
    k.response = k.session.post(url, data = data, headers = headers, timeout = 2)
    resp = k.response.json()['result']
    return resp[asset]



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
    #print(k.response.status_code,"  ",k.response.json())

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
            'prices': [],
            'ema'   : []
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
            #print(crypto_data)
            if len(crypto_data)>1:
                if len(trades[pair]) > 0:
                    if trades[pair][-1]['sold'] or trades[pair][-1]==None:
                        # Check if we should buy
                        check_data(pair,crypto_data,True)
                    if trades[pair][-1]['bought']:
                        # Check if we should sell
                        check_data(pair,crypto_data,False)
                else:
                    check_data(pair,crypto_data,True)
            save_eq_balance_1(pair,crypto_data)
            time.sleep(round(((60-len(pairs))/len(pairs))/2))


def check_data(name, crypto_data, should_buy):
    high = 0
    low = 0
    close = 0
    #print(len(crypto_data))
    for b in crypto_data[-100:]:
        if b not in mva[name]['prices']:
            mva[name]['prices'].append(b)
        high += float(b[2])
        low += float(b[3])
        close += float(b[4])

    df = pd.DataFrame(crypto_data)
    df['EMA1'] = df.iloc[:,4].ewm(span=1,adjust=False).mean()
    df['EMA2'] = df.iloc[:,4].ewm(span=2,adjust=False).mean()
    df['EMA3'] = df.iloc[:,4].ewm(span=5,adjust=False).mean()

    mva[name]['high'].append(high/100)
    mva[name]['low'].append(low/100)
    mva[name]['close'].append(close/100)
    mva[name]['ema1'] = df['EMA1'][-100:].to_list()
    mva[name]['ema2'] = df['EMA2'][-100:].to_list()
    mva[name]['ema3'] = df['EMA3'][-100:].to_list()

    save_crypto_data(mva)

    if should_buy:
        try_buy(mva[name],name,crypto_data)
    else:
        try_sell(mva[name],name,crypto_data)


def try_buy(data,name,crypto_data):
    # Analyse data to see if it is a good oportunity to buy
    make_trade = check_opportunity_ema(data,name,False,True)
    if make_trade:
        buy_crypto(crypto_data,name)


def buy_crypto(crypto_data,name):
    # Execute trade
    analysis_data = clear_crypto_data(name)
    # Make sure to make the trade before the next line of code
    # Find what we can buy for
    price = float(crypto_data[-1][4])
    funds = get_available_funds()
    if (funds>0):
        amount = rounddown(funds*(1/price),8)
        balance = update_balance(amount,name,price,False)
        save_trade(price,name,True,False,amount)
        print('Buy',amount,name,'at',price,'for',amount*price)
        print()


def api_buy_crypto(name,volume):
    urlpath = '/' + k.apiversion + '/private/AddOrder'
    url = k.uri + urlpath

    data = {}
    data['nonce'] = k.nonce
    data['pair'] = name
    data['type'] = 'buy'
    data['ordertype'] = 'market'
    data['volume'] = volume

    headers = {
        'API-Key'  : k.key,
        'API-Sign' : k._sign(data,urlpath)
    }

    api_update_nonce()
    try:
        k.response = k.session.post(url, data = data, headers = headers, timeout = 2)
        resp = k.response.json()['result']
        return resp
    except:
        return [[0, '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', 31]]


   
def try_sell(data,name,crypto_data):
    # Analyse data to see if it is a good oportunity to sell
    make_trade = check_opportunity_ema(data,name,True,False)
    if make_trade:
        sell_crypto(crypto_data,name)


def sell_crypto(crypto_data,name):
    balance = get_balance()
    analysis_data = clear_crypto_data(name)
    price = float(crypto_data[-1][4])
    #cryptos_not_owned += 1
    if (len(name)==8):
        amount = float(balance[name[:-4]])
    else:
        amount = float(balance[name[:-3]])
    balance = update_balance(amount,name,price,True)
    save_trade(price,name,False,True,amount)
    print('Sell',amount,name,'at',price,'for',amount*price)
    print()


#def api_sell_crypto():



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


def save_trade(close,name,bought,sold,amount):
    # Saves trades to json file
    trade = {
        'time_stamp'    :   str(int(time.time())),
        'price_eur'     :   close,
        'bought'        :   bought,
        'sold'          :   sold,
        'amount'        :   amount
    }
    print('TRADE:')
    print(json.dumps(trade,indent=4))
    trades = load_trades()
    trades[name].append(trade)
    with open('trades.json','w') as f:
        json.dump(trades,f,indent=4)


def check_opportunity_ema(data,name,sell,buy):
    if (len(data['ema2'])>5):
        above12 = []
        above13 = []
        arrema1 = data['ema1'][-5:]
        arrema2 = data['ema2'][-5:]
        arrema3 = data['ema3'][-5:]

        for i in range(len(arrema2)):
            if (arrema1[i] > arrema2[i]):
                above12.append(1)
            elif (arrema1[i] < arrema2[i]):
                above12.append(-1)
            else: 
                above12.append(0)


        for i in range(len(arrema2)):
            if (arrema1[i] > arrema3[i]):
                above13.append(1)
            elif (arrema1[i] < arrema3[i]):
                above13.append(-1)
            else: 
                above13.append(0)

        k121 = 0
        k122 = 0
        for value in above12:
            k122 = k121
            k121 = value

        k131 = 0
        k132 = 0
        for value in above13:
            k132 = k131
            k131 = value

        i = 0
        i1 = 0
        iGo = False
        for value in reversed(above12):
            if (i==0 and i1==0):
                if (value==1):
                    i = value
                else:
                    i = -1
            if (i==1 and i1==0 and value==-1):
                i1 = value
        if (i==1 and i1==-1):
            iGo = True

        j = 0
        j1 = 0
        jGo = False
        for value in reversed(above13):
            if (j==0 and j1==0):
                if (value==1):
                    j = value
                else:
                    j = -1
            if (j==1 and j1==0 and value==-1):
                j1 = value
        if (j==1 and j1==-1):
            jGo = True

        
    
        if (sell and k122==1 and k121==-1):
            return True
        
        if (buy and iGo and jGo):
            return True

    return False


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

def save_eq_balance(pair,data):
    now = datetime.datetime.now()
    nowstr = now.strftime("%Y-%m-%d %H:%M:%S")

    balance = get_balance()

    eqbal = {}
    eqbal1 = {}

    eqbal1[nowstr] = {}

    with open('eqbalance.json','r') as f:
        try:
            eqbal = json.load(f)
        except:
            eqbal = {}

    try: 
        eqbal1[nowstr]['ZEUR'] = float(balance['ZEUR'])
    except:
        eqbal1[nowstr]['ZEUR'] = 0.0

    datai = data[-1]

    for bal in eqbal:
        if bal[:-4] in balance:
            eqbal1[nowstr][bal] = eqbal[bal]
        if bal[:-3] in balance:
            eqbal1[nowstr][bal] = eqbal[bal]

    pair1 = pair[:-3]
    if pair1 in balance:
        eqbal1[nowstr][pair] = float(datai[4]) * float(balance[pair1])

    pair1 = pair[:-4]
    if pair1 in balance:
        eqbal1[nowstr][pair] = float(datai[4]) * float(balance[pair1])

    sumbalance = 0.0
    for value in eqbal1[nowstr]:
        if (value=='TOT'):
            pass
        else:
            sumbalance += float(eqbal1[nowstr][value])

    eqbal1[nowstr]['TOT'] = sumbalance

    eqbal[nowstr] = eqbal1[nowstr]

    print(eqbal1)

    with open('eqbalance.json','w') as f:
        json.dump(eqbal,f,indent=4)



def save_eq_balance_1(pair,data):
    now = datetime.datetime.now()
    nowstr = now.strftime("%Y-%m-%d %H:%M:%S")

    balance = get_balance()

    eqbal = {}
    with open('eqbalance.json','r') as f:
        try:
            eqbal = json.load(f)
        except:
            eqbal = {}

    try:
        eqbal[nowstr] = eqbal[list(eqbal.keys())[-1]]
    except:
        eqbal[nowstr] = {}

    datai = data[-1]
    for bal in balance:
        if (bal=='ZEUR'):
            eqbal[nowstr]['ZEUR'] = float(balance['ZEUR'])
        if (bal==pair[:-3]):
            eqbal[nowstr][pair[:-3]] = float(datai[4]) * float(balance[bal])
        if (bal==pair[:-4]):
            eqbal[nowstr][pair[:-4]] = float(datai[4]) * float(balance[bal])

    try:
        eqbal[nowstr].pop('TOT')
    except:
        pass

    keys2remove = []
    for bal in eqbal[nowstr]:
        if bal not in balance:
            keys2remove.append(bal)

    for bal in keys2remove:
        eqbal[nowstr].pop(bal)

    sumbalance = 0.0
    for value in eqbal[nowstr]:
        if (value=='TOT'):
            pass
        else:
            sumbalance += float(eqbal[nowstr][value])
    eqbal[nowstr]['TOT'] = sumbalance

    print(nowstr,eqbal[nowstr])

    with open('eqbalance.json','w') as f:
        json.dump(eqbal,f,indent=4)




def rounddown(number,decimals):
    return math.floor(number*(10**decimals))/(10**decimals)



if __name__ == '__main__':
    k = krakenex.API()
    k.load_key('kraken.key')
    api_update_nonce()
    pairs = get_pairs()
    since = str(int(time.time()-43200))
    mva = load_crypto_data_from_file()

    #ticker = api_get_ticker_ohlc_test('XXBTZEUR',since)
    #for b in ticker[-100:]:
    #    print(b)
    #print(ticker)

    bot(since,k,pairs)
