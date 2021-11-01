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
ainttime = ['1m','5m','15m']
ainttime = ['5m']
intperiod = '2d'

cryptos = ['YFI-EUR']
cryptos = ['YFI-EUR','DOGE-EUR']
cryptos = ['DOGE-EUR','YFI-EUR']
#cryptos = ['XLM-EUR','YFI-EUR','BTC-EUR','DOGE-EUR']
cryptos = ['YFI-EUR']
cryptos = ['BTC-EUR']


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


def check_ema(aboveij,updown):
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

def check_rsi(rsi,updown):
    #delta = data.diff()
    #up = delta.clip(lower=0)
    #down = -1*delta.clip(upper=0)
    #ema_up = up.ewm(com=winl,adjust=False).mean()
    #ema_down = down.ewm(com=winl,adjust=False).mean()
    #rs = ema_up/ema_down
    #rsi = rs.iat[-1]

    if ((updown==True and rsi<=30) or (updown==False and rsi>=70)):
        return True
    else:
        return False


def check_opportunity(data,name,sell,buy):
    nth = 5
    if (len(data['ema2'])>=nth):
        above12 = []
        above13 = []
        above23 = []
        arrema1 = data['ema1'][-nth:]
        arrema2 = data['ema2'][-nth:]
        arrema3 = data['ema3'][-nth:]

        for i in range(len(arrema2)):
            if (arrema1[i] > arrema2[i]):
                above12.append(1)
            else:
                above12.append(-1)
            if (arrema1[i] > arrema3[i]):
                above13.append(1)
            else:
                above13.append(-1)
            if (arrema2[i] > arrema3[i]):
                above23.append(1)
            else:
                above23.append(-1)

        dltarrema1 = max(arrema1) - min(arrema1)
        avgarrema1 = sum(arrema1) / len(arrema1)
        
        ema_u_go12, ema_u_pos12 = check_ema(above12,1)
        ema_u_go13, ema_u_pos13 = check_ema(above13,1)
        ema_u_go23, ema_u_pos23 = check_ema(above23,1)
        ema_d_go12, ema_d_pos12 = check_ema(above12,-1)

        slope3_2 = arrema3[-1] - arrema3[-3]

        #rsi_go = check_rsi(data['rs'][-1],buy)
        #rsi_go = True

        if (buy and ema_u_go23 and ema_u_pos23<=ema_d_pos12 and (dltarrema1>0.003*avgarrema1) and slope3_2>0):
            return True

        #if (sell and ema_d_go12 and ema_d_pos12<=ema_u_pos12 and ema_d_pos12<=ema_u_pos13):
        if (sell and ema_d_go12 and ema_d_pos12<=ema_u_pos12):
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

    fee = 0.00075

    trades = {}
    for crypto in cryptos:
        trades[crypto] = []

    pairs = []
    for i in range(2,10):
        for j in range(i+2,i+25):
            for k in range(j+2,j+50):
                pairs.append([i,j,k])

    best = {}
    trades = {}
    lastclose = 0.0
    bestcrypto = ''
    for crypto in cryptos:

        crypto1 = ''
        for cr in crypto:
            if cr != '-':
                crypto1 += cr

        if (bestcrypto==''):
            bestcrypto = crypto1

        if (len(best)==0):
            best[crypto1] = {'inttime':0,'ema1':0,'ema2':0,'ema3':0,'ZEUR':0.0}

        for inttime in ainttime:

            crypto_data_df = yf.download(tickers=crypto, period = intperiod, interval = inttime)
            crypto_data_df['idx'] = range(1,len(crypto_data_df)+1)

            #df1 = yf.download(tickers=crypto, start = "2021-05-31", end="2021-06-07", interval = inttime)
            #df2 = yf.download(tickers=crypto, start = "2021-05-24", end="2021-05-30", interval = inttime)
            #df3 = yf.download(tickers=crypto, start = "2021-05-17", end="2021-05-23", interval = inttime)
            #df4 = yf.download(tickers=crypto, start = "2021-05-10", end="2021-05-16", interval = inttime)
            #df5 = yf.download(tickers=crypto, start = "2021-05-3", end="2021-05-9", interval = inttime)
            #df6 = yf.download(tickers=crypto, start = "2021-04-26", end="2021-05-2", interval = inttime)
            #df7 = yf.download(tickers=crypto, start = "2021-04-19", end="2021-04-25", interval = inttime)
            #df8 = yf.download(tickers=crypto, start = "2021-04-12", end="2021-04-18", interval = inttime)
            #crypto_data_df = pd.concat([df8,df7,df6,df5,df4,df3,df2,df1])
            #crypto_data_df = pd.concat([df3,df2,df1])

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

                rsith = ema3

                df = pd.DataFrame(crypto_data_df)
                df['EMA1'] = df.iloc[:,4].ewm(span=ema1,adjust=False).mean()
                df['EMA2'] = df.iloc[:,4].ewm(span=ema2,adjust=False).mean()
                df['EMA3'] = df.iloc[:,4].ewm(span=ema3,adjust=False).mean()
                df['values']   =    df.iloc[:,4].astype(float)
                df['delta']    =    df['values'].diff()
                df['up']       =    df['delta'].clip(lower=0)
                df['down']     = -1*df['delta'].clip(upper=0)
                df['ema_up']   =    df['up'].ewm(com=rsith,adjust=False).mean()
                df['ema_down'] =    df['down'].ewm(com=rsith,adjust=False).mean()
                df['rs']       =    df['ema_up']/df['ema_down']

                mva[crypto]['close'] = df['Close'].to_list()
                mva[crypto]['high'] = df['High'].to_list()
                mva[crypto]['low'] = df['Low'].to_list()
                mva[crypto]['ema1']  = df['EMA1'].to_list()
                mva[crypto]['ema2']  = df['EMA2'].to_list()
                mva[crypto]['ema3']  = df['EMA3'].to_list()
                mva[crypto]['rs'] = df['rs'].to_list()

                periodspan = 5

                for it in range(ema3,len(crypto_data_df)-periodspan):
                
                    mva1 = {}
                    mva1[crypto] = {
                        'close' : mva[crypto]['close'][:it+periodspan],
                        'high' :  mva[crypto]['high'][:it+periodspan],
                        'low' :   mva[crypto]['low'][:it+periodspan],
                        'ema1' :  mva[crypto]['ema1'][:it+periodspan],
                        'ema2' :  mva[crypto]['ema2'][:it+periodspan],
                        'ema3' :  mva[crypto]['ema3'][:it+periodspan],
                        'rs'   :  mva[crypto]['rs'][:it+periodspan]
                    }
                    
                    if len(trades[crypto]) > 0:
                        # Buy
                        if trades[crypto][-1]['sold'] or trades[crypto][-1]==None:
                            make_trade = check_opportunity(mva1[crypto],crypto,False,True)
                            if make_trade:
                                buy_crypto(mva1[crypto],crypto)
                        # Sell
                        if trades[crypto][-1]['bought']:
                            make_trade = check_opportunity(mva1[crypto],crypto,True,False)
                            if make_trade:
                                sell_crypto(mva1[crypto],crypto)
                    else:
                        # Buy
                        make_trade = check_opportunity(mva1[crypto],crypto,False,True)
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

                balancei = rounddown(balancei1 + balancei2,4)
                if (balancei>best[bestcrypto]['ZEUR']):
                    if (crypto1!=bestcrypto):
                        best = {}
                        bestcrypto = crypto1
                    best[bestcrypto] = {
                        'inttime' : int(inttime[:-1]),
                        'ema1' : ema1,
                        'ema2' : ema2,
                        'ema3' : ema3,
                        'ZEUR' : balancei
                    }
                print(crypto1,inttime,pair,'\t',best)

    report_go('Params computed:' + str(best))
    with open('/home/icirauqui/share/TBotB/params.json','w') as f:
        json.dump(best,f,indent=4)
