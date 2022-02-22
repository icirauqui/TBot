import sys
import json
import time
import math
import pandas as pd
import numpy as np

from keys import *
from api_binance import *




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
    
    global inttime, ema1, ema2, ema3, warn1, warnth

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
            if (warn1<warnth):
                warn1 += 1
                tlmsg = 'Might buy ' + str(warn1) + ' of ' + str(warnth)
                print(tlmsg)
            else:
                api_buy_crypto(name)
                api_eq_balance(True)
                warn1 = 0
                print()
                #time.sleep(30)
        elif (warn1>0):
            warn1 = 0
            tlmsg = 'Buy averted ' + str(warn1) + ' of ' + str(warnth)
            print(tlmsg)
    else:
        make_trade = check_opportunity(mva,name,True,False)
        if make_trade:
            if (warn1<warnth):
                warn1 += 1
                tlmsg = 'Might sell ' + str(warn1) + ' of ' + str(warnth)
                print(tlmsg)
            else:
                api_sell_crypto(name)
                api_eq_balance(True)
                warn1 = 0
                print()
                #time.sleep(60)
        elif (warn1>0):
            warn1 = 0
            tlmsg = 'Sell averted ' + str(warn1) + ' of ' + str(warnth)
            print(tlmsg)






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
        ema_d_go13, ema_d_pos13 = check_ema(above13,-1)
        ema_d_go23, ema_d_pos23 = check_ema(above23,-1)

        slope_1 = (arrema1[-1]-arrema1[-3]) / arrema1[-3]
        slope_2 = (arrema2[-1]-arrema2[-3]) / arrema2[-3]
        slope_3 = (arrema3[-1]-arrema3[-3]) / arrema3[-3]

        if (buy):
            if ( (ema_u_go12 and ema_u_pos12<=ema_d_pos12 and ema_u_go13 and ema_u_pos13<=ema_d_pos13) or
                 (ema_u_go23 and ema_u_pos23<=ema_d_pos23 and arrema2[-1]>1.002*arrema3[-1]) or
                 (ema_u_go12 and ema_u_pos12<=ema_d_pos12 and arrema2[-1]>1.004*arrema3[-1] and slope_3>0.05) or
                 (arrema1[-1]>1.005*arrema2[-1] and arrema2[-1]>1.010*arrema3[-1] and 
                  arrema1[-2]>1.005*arrema2[-2] and arrema2[-2]>1.010*arrema3[-2] and 
                  arrema1[-3]>1.005*arrema2[-3] and arrema2[-3]>1.010*arrema3[-3])    ):
                return True
        if (sell):
            if ( (ema_d_go12 and ema_d_pos12<=ema_u_pos23 and arrema1[-1]<=0.99*arrema2[-1]) or
                 (ema_d_go13 and ema_d_pos13<=ema_u_pos13 ) or 
                 (ema_d_go23 and ema_d_pos23<=ema_u_pos23 )):
                return True

    return False




if __name__ == '__main__':

    report_go('Initializing TBotB...')
    print('Initializing TBotB...')

    #k = Client(api_key,api_secret)
    api = api_binance(api_key, api_secret)
    pair = get_pairs()

    # Start params
    inttime = '1m'
    ema1 = 3
    ema2 = 7
    ema3 = 14
    izeur = 100.0

    profit = 0.0

    warn1 = 0
    warnth = 0

    #pair = get_pairs()
    #get_asset_params(pair,bInit)
    #print('Pair =',pair,'  Params =',inttime,ema1,ema2,ema3,izeur,60*inttime)

    errorcode = 0

    # BOT
    api.api_eq_balance(True)
    bInit = True
    while True:
        try:
            print()
            
            errorcode = 0
            ordertopup = api.topup_bnb(0.01,0.05)
            
            errorcode = 1 
            # Update parameters if no crypto is held
            actbal = api.api_count_active_balances()
            if (actbal<=2 or bInit==True):
                pair = get_pairs()
                get_asset_params(pair,bInit)
                bInit = False
            print('Pair =',pair,'  Params =',inttime,ema1,ema2,ema3,izeur,60*inttime)
            
            errorcode = 2
            # Fetch historical data and recent trades
            since = str(int(time.time()-43200)*1000)
            crypto_data = api.api_get_ticker_ohlc(pair,since,inttime)
            trades = api.api_get_all_orders(pair)

            errorcode=3
            # Check market and buy/sell
            if len(crypto_data) > 1:
                if len(trades) > 0:
                    errorcode = 4
                    if (trades[-1]['side']=='SELL' and izeur > 100.0):  # try buy
                        check_data(pair,crypto_data,True)
                    elif (trades[-1]['side']=='BUY'):                    # try sell
                        check_data(pair,crypto_data,False)
                else:
                    errorcode = 5
                    if (izeur > 100.0):
                        check_data(pair,crypto_data,True)       # try buy

            # Report and hold
            api.api_eq_balance(False)
            time.sleep(60)

        except:
            print('ERROR: Global' + str(errorcode))
            report_go('ERROR: Global' + str(errorcode))
            time.sleep(5)
