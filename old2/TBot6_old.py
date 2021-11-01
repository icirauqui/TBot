import krakenex
from pykrakenapi import KrakenAPI
import time
import decimal
import json

from tbot6_mysql import *

api_key_desc = 'api-key-1618654051368'
api_key_main = 'TxvFOKl15RVkyMmQmftuZC/d7KOnB7gn0mxwy5qqI8gB0+3Ho7KaRetv'
api_key_private = 'MGVtVhjmjgAGMonnFzF9qBS0YvBi3aDnEBOB03H11SqSImlOhWd15kjJ873MOjAEPvLbgqdm5XrP1C86AMtqXw=='

def now():
    return decimal.Decimal(time.time())

def get_balance():
    with open('balance.json', 'r') as f:
        try:
            return json.load(f)
        except:
        # add query to SQL DB and check against API
            return{'ZUSD' : '1000.0', 'EUR.HOLD' : '0.0000'}
    #print(k.query_private('Balance')['result'])
    #return k.query_private('Balance')['result'])



def get_available_funds():
    balance = get_balance()
    money = float(balance['ZUSD'])
    cryptos_not_owned = 6 - (len(balance)-2)
    funds = money / cryptos_not_owned
    return funds


def update_balance(amount, name, price, sold):
    balance = get_balance()
    if sold:
        balance.pop(name[:-4], None)
        balance['ZUSD'] = str(float(balance['ZUSD']) + (amount*price))
    else:
        balance['ZUSD'] = str(float(balance['ZUSD']) - (amount*price))
    save_balance(balance)
    return balance

# Get the price data for the crypto
def get_crypto_data(pair,since):
    ret = k.query_public('OHLC', data = {'pair':pair, 'since':since})
    return ret['result'][pair]

def get_purchasing_price(name):
    trades = load_trades()
    return trades[name][-1]['price_usd']




def get_pairs():
    return ['XETHZUSD']


def main():
    connection = create_db_connection(sqlhost,sqluser,sqlpass,sqldb)

    k = krakenex.API()
    k.load_key('kraken.key')

    print(now())

    

    
    #print(k.query_private('Balance'))

    # pairs = get_pairs()
    # since = str(int(time.time()-43200))
    # print(since)
    # time.sleep(2)

main()


