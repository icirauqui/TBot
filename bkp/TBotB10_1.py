import sys
import json
import time
import math
import datetime
import pandas as pd
import numpy as np

import plotly
import telegram_send

from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException




def api_get_balance():
    baltemp = {}
    try:
        balancei = k.get_asset_balance(asset='EUR')
        baltemp['EUR'] = [balancei['free'],balancei['locked']]

        global pair
        pairi = pair[:-3]
        try:
            balancei = k.get_asset_balance(asset=pairi)
            baltemp[pair] = [balancei['free'],balancei['locked']]
        except BinanceAPIException as e:
            print('BinanceAPIException',e)
        except BinanceOrderException as e:
            print('BinanceOrderException',e)
        return baltemp
    except BinanceAPIException as e:
        print('BinanceAPIException',e)
    except BinanceOrderException as e:
        print('BinanceOrderException',e)



def get_available_funds():
    balance = api_get_balance()
    try:
        funds = float(balance['EUR'][0]) + float(balance['EUR'][1])
        fee = 0.0010
        #fundsfee = funds * (1-(2*fee))
        fundsfee = funds * 0.99
        funds1 = rounddown(fundsfee,0)
        return funds1
    except:
        return 0.0


def api_get_ticker_ohlc(asset,since,inttime):
    try:
        data = k.get_historical_klines(asset, str(inttime) + 'm', since, limit=1000)
        return data
    except:
        return [[0, '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', 31]]


def api_get_trades(asset):
    trades = k.get_my_trades(symbol=asset)
    return trades


def api_get_all_orders(asset):
    orders = k.get_all_orders(symbol=asset, limit=100)
    return orders


def get_pairs():
    with open('params.json','r') as f:
        try:
            pcr = json.load(f)
            crypto = ''
            for pcri in pcr:
                crypto = pcri
            return crypto
        except:
            pass




def get_asset_params(name,init):
    try:
        params = {}
        global inttime, ema1, ema2, ema3, izeur
        if (init==True):
            with open('params1.json','r') as f:
                try:
                    params = json.load(f)
                    inttime = int(params[name]['inttime'])
                    ema1 = int(params[name]['ema1'])
                    ema2 = int(params[name]['ema2'])
                    ema3 = int(params[name]['ema3'])
                    izeur = float(params[name]['ZEUR'])
                except:
                    pass
        else:
            with open('params.json','r') as f:
                try:
                    params = json.load(f)

                    with open('params1.json','w') as f:
                        try:
                            json.dump(params,f,indent=4)
                        except:
                            pass

                    inttime1 = int(params[name]['inttime'])
                    ema11 = int(params[name]['ema1'])
                    ema21 = int(params[name]['ema2'])
                    ema31 = int(params[name]['ema3'])
                    izeur1 = float(params[name]['ZEUR'])

                    if (inttime != inttime1 or ema1 != ema11 or ema2 != ema21 or ema3 != ema31):
                        print('Params updated =',inttime1,ema11,ema21,ema31)
                        msg1 = 'Params updated = ' + str(params)
                        report_go(msg1)

                    inttime = int(params[name]['inttime'])
                    ema1 = int(params[name]['ema1'])
                    ema2 = int(params[name]['ema2'])
                    ema3 = int(params[name]['ema3'])
                    izeur = float(params[name]['ZEUR'])
                
                except:
                    pass
    
    except:
        report_go('ERROR: Updating params')



def check_data(name, crypto_data, should_buy):
    
    global inttime, ema1, ema2, ema3

    mva = {
        'prices' : [],
        'ema1'   : [],
        'ema2'   : [],
        'ema3'   : [],
        'rs'     : []
    }

    for b in crypto_data[-100:]:
        if b not in mva['prices']:
            mva['prices'].append(b)

    df = pd.DataFrame(crypto_data)

    # EMA
    df['EMA1']     = df.iloc[:,4].ewm(span=ema1,adjust=False).mean()
    df['EMA2']     = df.iloc[:,4].ewm(span=ema2,adjust=False).mean()
    df['EMA3']     = df.iloc[:,4].ewm(span=ema3,adjust=False).mean()

    # RSI
    rsith = ema3
    df['values']   =    df.iloc[:,4].astype(float)
    df['delta']    =    df['values'].diff()
    df['up']       =    df['delta'].clip(lower=0)
    df['down']     = -1*df['delta'].clip(upper=0)
    df['ema_up']   =    df['up'].ewm(com=rsith,adjust=False).mean()
    df['ema_down'] =    df['down'].ewm(com=rsith,adjust=False).mean()
    df['rs']       =    df['ema_up']/df['ema_down']

    mva['ema1'] = df['EMA1'][-100:].to_list()
    mva['ema2'] = df['EMA2'][-100:].to_list()
    mva['ema3'] = df['EMA3'][-100:].to_list()
    mva['rs']   = df['rs'][-100:].to_list()

    if should_buy:
        make_trade = check_opportunity(mva,name,False,True)
        if make_trade:
            api_buy_crypto(name)
            api_eq_balance(True)
            print()
            time.sleep(30)
    else:
        make_trade = check_opportunity(mva,name,True,False)
        if make_trade:
            api_sell_crypto(name)
            api_eq_balance(True)
            print()
            time.sleep(60)


def api_buy_crypto(name):
    # Check if there are any sell orders ongoing and cancel them
    try:
        orders = k.get_open_orders(symbol=name)
        if (len(orders)>0):
            for order in orders:
                try:
                    cancel = k.cancel_order(symbol=name,orderId=order['orderId'])
                    #telegram_send.send(messages=['B ',cancel])
                    report_go(cancel)
                    orders = k.get_open_orders(symbol=name)
                except BinanceAPIException as e:
                    print('BinanceAPIException',e)
                    report_go('ERROR'+str(e))
                except BinanceOrderException as e:
                    print('BinanceOrderException',e)
                    report_go('ERROR'+str(e))
    except BinanceAPIException as e:
        print('BinanceAPIException',e)
        report_go('ERROR'+str(e))
    except BinanceOrderException as e:
        print('BinanceOrderException',e)
        report_go('ERROR'+str(e))

    # Purchase with available funds
    try:
        price = api_get_ticker(name)
        funds = get_available_funds()
        amount = 0.0
        if (funds>0):
            if (name=='DOGEEUR'):
                amount = rounddown(funds*(1/price),1)
            else:
                amount = rounddown(funds*(1/price),6)
                
            try:
                trorder = k.create_order(symbol=name,side='BUY',type='MARKET',quantity=str(amount))
                tlmsg = trorder['side'] + '-' + trorder['symbol'] + '\n' + trorder['fills'][0]['qty'] + ' ' + name[0:3] + '\n' + trorder['cummulativeQuoteQty'] + ' EUR' + '\n' + trorder['fills'][0]['commission'] + ' ' + trorder['fills'][0]['commissionAsset']
                #telegram_send.send(messages=['B ',tlmsg])
                report_go(tlmsg)
                print()
                print('BUY',amount,name,'at',price,'for',amount*price*0.999)

                global profit
                profit = amount*price*1.0010

            except BinanceAPIException as e:
                print('BinanceAPIException',e)
                #telegram_send.send(messages=['B ',e])
                report_go('ERROR'+str(e))
            except BinanceOrderException as e:
                print('BinanceOrderException',e)
                #telegram_send.send(messages=['B ',e])
                report_go('ERROR'+str(e))
    except BinanceAPIException as e:
        print('BinanceAPIException',e)
    except BinanceOrderException as e:
        print('BinanceOrderException',e)



def api_sell_crypto(name):
    # Check if there are any buy orders ongoing and cancel them
    try:
        orders = k.get_open_orders(symbol=name)
        if (len(orders)>0):
            for order in orders:
                try:
                    cancel = k.cancel_order(symbol=name,orderId=order['orderId'])
                    telegram_send.send(messages=['B ',cancel])
                    orders = k.get_open_orders(symbol=name)
                except BinanceAPIException as e:
                    print('BinanceAPIException',e)
                    report_go('ERROR'+str(e))
                except BinanceOrderException as e:
                    print('BinanceOrderException',e)
                    report_go('ERROR'+str(e))
    except BinanceAPIException as e:
        print('BinanceAPIException',e)
        report_go('ERROR'+str(e))
    except BinanceOrderException as e:
        print('BinanceOrderException',e)
        report_go('ERROR'+str(e))

    # Sell crypto balance
    try:
        balance = api_get_balance()
        price = api_get_ticker(name)
        amount = 0.0
        if (float(balance[name][0])>0.0 and float(balance[name][1])==0.0):
            if (name=='DOGEEUR'):
                amount = rounddown(float(balance[name][0]),1)
            else:
                amount = rounddown(float(balance[name][0]),6)

            try:
                trorder = k.create_order(symbol=name,side='SELL',type='MARKET',quantity=str(amount))
                global profit
                profit1 = amount*price*0.999 - profit
                tlmsg = trorder['side'] + '-' + trorder['symbol'] + '\n' + trorder['fills'][0]['qty'] + ' ' + name[0:3] + '\n' + trorder['cummulativeQuoteQty'] + ' EUR' + '\n' + trorder['fills'][0]['commission'] + ' ' + trorder['fills'][0]['commissionAsset'] + '\nProfit = ' + str(rounddown(profit1,2))
                report_go(tlmsg)
                print()
                print('SELL',amount,name,'at',price,'for',amount*price*0.999)
            except BinanceAPIException as e:
                print('BinanceAPIException',e)
                report_go('ERROR'+str(e))
            except BinanceOrderException as e:
                print('BinanceOrderException',e)
                report_go('ERROR'+str(e))
    except BinanceAPIException as e:
        print('BinanceAPIException',e)
    except BinanceOrderException as e:
        print('BinanceOrderException',e)



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

        if (buy):
            if (ema_u_go23 and ema_u_pos23<=ema_d_pos12 and (dltarrema1>0.003*avgarrema1)):
                return True
            else:
                print('BUY - Cross =',ema_u_go23,'- dlt1-avg1 =',rounddown(dltarrema1,3),'-',rounddown(0.003*avgarrema1,3))

        if (sell and ema_d_go12 and ema_d_pos12<=ema_u_pos12):
            return True

    return False


def api_eq_balance(bTelegram):
    now = datetime.datetime.now()
    nowstr = now.strftime("%Y-%m-%d %H:%M:%S")

    balance = api_get_balance()
    eqbal = {}

    totbal = 0.0

    eqbalmsg = str(nowstr)
    for bal in balance:
        baltemp = float(balance[bal][0]) + float(balance[bal][1])
        if (bal!='EUR'):
            tick = api_get_ticker(bal)
            baltemp *= tick
        baltemp1 = rounddown(baltemp,2)
        eqbalmsg += '\n      ' + str(bal) + ': ' + str(baltemp1)
        totbal += baltemp1
        eqbal[bal] = baltemp1
    
    eqbalmsg += '\n      ' + 'TOT' + ': ' + str(rounddown(totbal,2))
    eqbal['TOT'] = rounddown(totbal,2)

    print(nowstr,eqbal)

    if (bTelegram):
        report_go(eqbalmsg)



def api_get_ticker(pair):
    tick = k.get_symbol_ticker(symbol=pair)
    return float(tick['price'])



def report_go(extradata):
    now = datetime.datetime.now()
    nowstr = now.strftime("%Y-%m-%d %H:%M:%S")
    eqbalmsg = 'B ' + str(nowstr) + '\n' + str(extradata)
    telegram_send.send(messages=[eqbalmsg])



def rounddown(number,decimals):
    return math.floor(number*(10**decimals))/(10**decimals)


def api_count_active_balances():
    try:
        act = k.get_account()
        balances = act['balances']
        cntpairs = 0
        for acti in balances:
            actibal = float(acti['free']) + float(acti['locked'])
            if (acti['asset']=='YFI' and actibal>0.00001):
                cntpairs += 1
            elif (acti['asset']=='DOGE' and actibal>0.1):
                cntpairs += 1
            elif (acti['asset']!='YFI' and acti['asset']!='DOGE' and actibal>0.00001):
                cntpairs += 1
        return cntpairs
    except:
        report_go('ERROR balance count')
        return 1




def topup_bnb(min_balance: float, topup: float):
	bnb_balance = k.get_asset_balance(asset='BNB')
	bnb_balance = float(bnb_balance['free'])
    price = api_get_ticker('BNBEUR')
	if bnb_balance < min_balance:
		qty = round(topup - bnb_balance, 5)
        tlgmsg = 'TOPUP BNB - ' + str(qty) + ' - ' + str(roundown(price,2)) + ' - ' + str(rounddown(price*qty,2))
        print(tlgmsg)
        report_go(tlgmsg)
		order = k.order_market_buy(symbol='BNBEUR', quantity=qty)
		return order
	return False



if __name__ == '__main__':

    report_go('Initializing TBotB...')
    print('Initializing TBotB...')

    api_key = 'VATMASRoF3nWv4FFQrMk3sVeeqGuyYeLDXu7LPUWCfwyCXXlu3BcqeYOtFuhM9bJ'
    api_secret = 'pAydgRDbaDlYQ4oDYkKDVqjtlqhdH3vYdVJOcfBLL3069xZDAk3Q0boyTUOdyMn2'
    k = Client(api_key,api_secret)
    pair = get_pairs()

    # Start params
    inttime = '1m'
    ema1 = 3
    ema2 = 7
    ema3 = 14
    izeur = 100.0

    profit = 0.0

    # BOT
    api_eq_balance(True)
    bInit = True
    while True:
        try:
            print()

            # Update parameters if no crypto is held
            actbal = api_count_active_balances()
            if (actbal==1 or bInit==True):
                pair = get_pairs()
                get_asset_params(pair,bInit)
                bInit = False
            print('Pair =',pair,'  Params =',inttime,ema1,ema2,ema3,izeur)
            
            # Fetch historical data and recent trades
            since = str(int(time.time()-43200)*1000)
            crypto_data = api_get_ticker_ohlc(pair,since,inttime)
            trades = api_get_all_orders(pair)

            # Check market and buy/sell
            if len(crypto_data) > 1:
                if len(trades) > 0:
                    if (trades[-1]['side']=='SELL' and izeur > 100.0):  # try buy
                        check_data(pair,crypto_data,True)
                    elif (trades[-1]['side']=='BUY'):                    # try sell
                        check_data(pair,crypto_data,False)
                else:
                    if (izeur > 100.0):
                        check_data(pair,crypto_data,True)       # try buy

            # Report and hold
            api_eq_balance(False)
            time.sleep(20)

        except:
            print('ERROR: Global')
            report_go('ERROR: Global')
            time.sleep(5)
