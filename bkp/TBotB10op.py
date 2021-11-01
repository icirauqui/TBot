import sys

import json
import time
import math
import datetime

import pandas as pd
import numpy as np

import yfinance as yf
import plotly

import telegram_send

blive = True

ema1 = 2
ema2 = 3
ema3 = 6

irange = 10
jrange = 20
krange = 50

ainttime = ['1m','2m','5m','15m','30m','60m','90m','1d']
ainttime = ['5m']
intperiod = '2d'

cryptos = ['XLM-EUR','YFI-EUR','BTC-EUR']
cryptos = ['YFI-EUR']


global balance 
balance = {
    'ZEUR'  : '100.0',
}


def get_balance():
    return balance


def report_go(extradata):
    now = datetime.datetime.now()
    nowstr = now.strftime("%Y-%m-%d %H:%M:%S")
    eqbalmsg = 'B ' + str(nowstr) + '\n' + extradata
    telegram_send.send(messages=[eqbalmsg])


def rounddown(number,decimals):
    return math.floor(number*(10**decimals))/(10**decimals)


def compute_rsi(data1,winl=10):
    data = pd.DataFrame.from_dict(data1)

    #calculate the return of the day and add as new column
    data['return'] = np.log(data['close'] / data['close'].shift(1) )

    #calculate the movement on the price compared to the previous day closing price
    data['movement'] = data['close'] - data['close'].shift(1)
    data['up'] = np.where((data['movement'] > 0) ,data['movement'],0)
    data['down'] = np.where((data['movement'] < 0) ,data['movement'],0)

    #calculate moving average of the last winl days gains and losses
    up = data['up'].rolling(winl).mean()
    down = data['down'].abs().rolling(winl).mean()
    RS = up / down
    RSI = 100.0 - (100.0 / (1.0 + RS))
    data['RSI'] = RSI

    data2 = data['RSI'].to_list()
    rsi1 = data2[-1]
    return rsi1


def compute_sine(datai):
    vector_1 = [60,datai['ema3'][9]-datai['ema3'][8]]
    vector_2 = [60,0]
    unit_vector_1 = vector_1 / np.linalg.norm(vector_1)
    unit_vector_2 = vector_2 / np.linalg.norm(vector_2)
    dot_product = np.dot(unit_vector_1, unit_vector_2)
    angle = np.arccos(dot_product)
    sine = math.sin(angle) 
    angle = angle * 180 / math.pi
    return sine


def get_action(aboveij,updown):
    i1 = 0
    i2 = 0
    cnti = 0
    cnti1 = 0
    initi1 = True
    initi2 = True
    iGo = False

    for value in reversed(aboveij):
        cnti1 += 1
        if (i1==0 and i2==0):
            i2 = value
        elif (i1==0 and value!=i2):
            i1 = value
            cnti = cnti1
    
    if (i1==0):
        cnti = cnti1
        if (i2==-1):
            i1=-1
    
        
    if ((updown==1 and i1<0 and i2>0) or (updown==-1 and i2<0)):
        return True,cnti
    else:
        return False,cnti


def check_opportunity_ema(data,name,sell,buy):
    if (len(data['ema2'])>=5):
        above12 = []
        above13 = []
        above23 = []
        arrema1 = data['ema1'][-5:]
        arrema2 = data['ema2'][-5:]
        arrema3 = data['ema3'][-5:]

        for i in range(len(arrema2)):
            if (arrema1[i] > arrema2[i]):
                above12.append(1)
            else:
                above12.append(-1)

        for i in range(len(arrema2)):
            if (arrema1[i] > arrema3[i]):
                above13.append(1)
            else:
                above13.append(-1)

        for i in range(len(arrema2)):
            if (arrema2[i] > arrema3[i]):
                above23.append(1)
            else:
                above23.append(-1)

        dltarrema1 = max(arrema1) - min(arrema1)
        avgarrema1 = sum(arrema1) / len(arrema1)
        
        iGo12,iPos12 = get_action(above12,1)
        iGo13,iPos13 = get_action(above13,1)
        jGo12,jPos12 = get_action(above12,-1)

        if (buy and iGo12 and iGo13 and iPos12<=jPos12 and iPos13<=jPos12 and (dltarrema1>0.0075*avgarrema1)):
            return True

        if (sell and jGo12 and jPos12<=iPos12 and jPos12<=iPos13):
            return True

    return False


def get_available_funds():
    money = float(balance['ZEUR'])
    funds = money
    funds = rounddown(funds,8)
    return funds


def update_balance(amount,name,price,sold):
    global fee
    if sold:
        balance['ZEUR'] = str(float(balance['ZEUR']) + (amount*price) - (amount*price*fee))
        balance.pop(name,None)
    else:
        balance['ZEUR'] = str(float(balance['ZEUR']) - amount*price - (amount*price*fee))
        balance[name] = str(amount)
    return balance


def save_trade(close,name,bought,sold,amount):
    trade = {
        'time_stamp'    :   str(int(time.time())),
        'price_eur'     :   close,
        'bought'        :   bought,
        'sold'          :   sold,
        'amount'        :   amount
    }
    trades[name].append(trade)


def buy_crypto(crypto_data,name):
    priceclose = float(crypto_data['close'][-1])
    pricehigh = float(crypto_data['high'][-1])
    price = (priceclose + pricehigh)/2
    price = pricehigh
    funds = get_available_funds()
    if (funds>0):
        amount = rounddown(funds*(1/price),8)
        balance = update_balance(amount,name,price,False)
        save_trade(price,name,True,False,amount)


def sell_crypto(crypto_data,name):
    priceclose = float(crypto_data['close'][-1])
    pricelow = float(crypto_data['low'][-1])
    price = (priceclose + pricelow)/2
    price = pricelow
    balance = get_balance()
    amount = float(balance[name])
    balance = update_balance(amount,name,price,True)
    save_trade(price,name,False,True,amount)


if __name__ == '__main__':
    mva = {}
    for name in cryptos:
        mva[name] = {
            'close' : [],
            'prices': [],
            'ema'   : []
        }

    fee = 0.0010

    trades = {}
    for crypto in cryptos:
        trades[crypto] = []

    pairs = []
    for i in range(1,10):
        for j in range(i+1,i+10):
            for k in range(j+3,j+30):
                pairs.append([i,j,k])

    best = {}
    trades = {}
    lastclose = 0.0
    for crypto in cryptos:

        crypto1 = ''
        if (crypto=='YFI-EUR'):
            crypto1 = 'YFIEUR'

        best[crypto1] = {'inttime':0,'ema1':0,'ema2':0,'ema3':0,'ZEUR':0.0}

        for inttime in ainttime:

            crypto_data_df_1 = yf.download(tickers=crypto, period = intperiod, interval = '1m')
            crypto_data_df = yf.download(tickers=crypto, period = intperiod, interval = inttime)
            crypto_data_df['idx'] = range(1,len(crypto_data_df)+1)

            for pair in pairs:

                balance = {
                    'ZEUR':'100.0'
                }
                trades[crypto] = []

                ema1 = pair[0]
                ema2 = pair[1]
                ema3 = pair[2]

                # Datetime Open High Low Close
                for b in crypto_data_df:
                    if b not in mva[crypto]['prices']:
                        mva[crypto]['prices'].append(b)

                df = pd.DataFrame(crypto_data_df)
                df['EMA1'] = df.iloc[:,4].ewm(span=ema1,adjust=False).mean()
                df['EMA2'] = df.iloc[:,4].ewm(span=ema2,adjust=False).mean()
                df['EMA3'] = df.iloc[:,4].ewm(span=ema3,adjust=False).mean()

                mva[crypto]['close'] = df['Close'].to_list()
                mva[crypto]['high'] = df['High'].to_list()
                mva[crypto]['low'] = df['Low'].to_list()
                mva[crypto]['ema1']  = df['EMA1'].to_list()
                mva[crypto]['ema2']  = df['EMA2'].to_list()
                mva[crypto]['ema3']  = df['EMA3'].to_list()

                periodspan = 10

                for it in range(len(crypto_data_df)-periodspan):
                
                    mva1 = {}
                    for iti in range(it,it+periodspan):
                        mva1[crypto] = {
                            'close' : mva[crypto]['close'][it:it+periodspan],
                            'high' : mva[crypto]['high'][it:it+periodspan],
                            'low' : mva[crypto]['low'][it:it+periodspan],
                            'ema1' : mva[crypto]['ema1'][it:it+periodspan],
                            'ema2' : mva[crypto]['ema2'][it:it+periodspan],
                            'ema3' : mva[crypto]['ema3'][it:it+periodspan]
                        }
                    
                    if len(trades[crypto]) > 0:
                        # Buy
                        if trades[crypto][-1]['sold'] or trades[crypto][-1]==None:
                            make_trade = check_opportunity_ema(mva1[crypto],crypto,False,True)
                            if make_trade:
                                buy_crypto(mva1[crypto],crypto)
                        # Sell
                        if trades[crypto][-1]['bought']:
                            make_trade = check_opportunity_ema(mva1[crypto],crypto,True,False)
                            if make_trade:
                                sell_crypto(mva1[crypto],crypto)
                    else:
                        # Buy
                        make_trade = check_opportunity_ema(mva1[crypto],crypto,False,True)
                        if make_trade:
                            buy_crypto(mva1[crypto],crypto)

                lastclose = mva[crypto]['close'][-1]

                balancei1 = 0.0
                try:
                    balancei1 = float(balance['ZEUR'])
                except:
                    pass

                balancei2 = 0.0
                try:
                    balancei2 = float(balance[crypto])*lastclose
                except:
                    pass

                balancei = balancei1 + balancei2
                if (balancei>best[crypto1]['ZEUR']):
                    best[crypto1] = {
                        'inttime' : int(inttime[:-1]),
                        'ema1' : ema1,
                        'ema2' : ema2,
                        'ema3' : ema3,
                        'ZEUR' : balancei
                    }
                print(inttime,pair,best)

    report_go('Params computed:' + str(best))
    with open('/home/icirauqui/share/TBotB/params.json','w') as f:
        json.dump(best,f,indent=4)
