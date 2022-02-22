from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException

import math
from api_telegram import *

def rounddown(number,decimals):
    return math.floor(number*(10**decimals))/(10**decimals)

class api_binance:
    def __init__(self, api_key, api_secret):
        print("Binance API starting...")
        self.k = Client(api_key, api_secret)

    def get_balance(self):
        baltemp = {}
        try:
            balancei = self.k.get_asset_balance(asset='EUR')
            baltemp['EUR'] = [balancei['free'],balancei['locked']]

            global pair
            pairi = pair[:-3]
            try:
                balancei = self.k.get_asset_balance(asset=pairi)
                baltemp[pair] = [balancei['free'],balancei['locked']]
            except BinanceAPIException as e:
                print('BinanceAPIException',e)
            except BinanceOrderException as e:
                print('BinanceOrderException',e)

            try:
                balancei = self.k.get_asset_balance(asset='BNB')
                baltemp['BNBEUR'] = [balancei['free'],balancei['locked']]
            except BinanceAPIException as e:
                print('BinanceAPIException',e)
            except BinanceOrderException as e:
                print('BinanceOrderException',e)

            return baltemp
        except BinanceAPIException as e:
            print('BinanceAPIException',e)
        except BinanceOrderException as e:
            print('BinanceOrderException',e)



    def get_available_funds(self):
        balance = self.get_balance()
        try:
            funds = float(balance['EUR'][0]) + float(balance['EUR'][1])
            fee = 0.0010
            #fundsfee = funds * (1-(2*fee))
            fundsfee = funds * 0.99
            funds1 = rounddown(fundsfee,0)
            return funds1
        except:
            return 0.0


    def api_get_ticker_ohlc(self, asset, since, inttime):
        try:
            data = k.get_historical_klines(asset, str(inttime) + 'm', since, limit=1000)
            return data
        except:
            return [[0, '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', '0.0000', 31]]


    def api_get_trades(self, asset):
        trades = k.get_my_trades(symbol=asset)
        return trades


    def api_get_all_orders(self, asset):
        orders = k.get_all_orders(symbol=asset, limit=100)
        return orders

    def api_buy_crypto(self, name):
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
            price = self.api_get_ticker(name)
            funds = self.get_available_funds()
            amount = 0.0
            if (funds>0):
                decpos = self.api_get_ticker_decimals(name)
                amount = rounddown(funds*(1/price),decpos)
                    
                try:
                    trorder = k.create_order(symbol=name,side='BUY',type='MARKET',quantity=str(amount))
                    tlmsg = trorder['side'] + '-' + trorder['symbol'] + '\n' + trorder['cummulativeQuoteQty'] + ' EUR'
                    #telegram_send.send(messages=['B ',tlmsg])
                    report_go(tlmsg)
                    print()
                    print('BUY',amount,name,'at',price,'for',amount*price*1.00075)

                    global profit
                    profit = amount*price*1.00075

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



    def api_sell_crypto(self, name):
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
            balance = self.get_balance()
            price = self.api_get_ticker(name)
            amount = 0.0
            if (float(balance[name][0])>0.0 and float(balance[name][1])==0.0):
                decpos = self.api_get_ticker_decimals(name)
                amount = rounddown(float(balance[name][0]),decpos)

                try:
                    trorder = k.create_order(symbol=name,side='SELL',type='MARKET',quantity=str(amount))
                    global profit
                    profit1 = amount*price*0.99925 - profit
                    tlmsg = trorder['side'] + '-' + trorder['symbol'] + '\n' + trorder['cummulativeQuoteQty'] + ' EUR' + '\nProfit = ' + str(rounddown(profit1,2))
                    report_go(tlmsg)
                    print()
                    print('SELL',amount,name,'at',price,'for',amount*price*0.99925)
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


    def api_eq_balance(self, bTelegram):
        now = datetime.datetime.now()
        nowstr = now.strftime("%Y-%m-%d %H:%M:%S")

        balance = self.get_balance()
        eqbal = {}

        totbal = 0.0

        eqbalmsg = str(nowstr)
        for bal in balance:
            baltemp = float(balance[bal][0]) + float(balance[bal][1])
            if (bal!='EUR'):
                tick = self.api_get_ticker(bal)
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

    def topup_bnb(self, min_balance: float, topup: float):
        bnb_balance = k.get_asset_balance(asset='BNB')
        bnb_balance = float(bnb_balance['free'])
        price = self.api_get_ticker('BNBEUR')
        if bnb_balance < min_balance:
            qty = round(topup - bnb_balance, 5)
            tlgmsg = 'TOPUP BNB - ' + str(qty) + ' - ' + str(rounddown(price,2)) + ' - ' + str(rounddown(price*qty,2))
            print(tlgmsg)
            report_go(tlgmsg)
            order = k.order_market_buy(symbol='BNBEUR', quantity=qty)
            return order
        return False


    def api_get_ticker_info(self, name):
        info = k.get_symbol_info(name)
        return info


    def api_get_ticker_decimals(self, name):
        info = k.get_symbol_info(name)
        prec = 0.0
        for i in info['filters']:
            if (i['filterType'] == 'LOT_SIZE'):
                prec = float(i['minQty'])
        for i in range(10):
            if (prec - rounddown(prec,i)==0):
                return i


    def api_count_active_balances(self):
        try:
            act = k.get_account()
            balances = act['balances']
            cntpairs = 0
            for acti in balances:
                actibal = float(acti['free']) + float(acti['locked'])
                if (acti['asset']=='YFI' and actibal>0.00001):
                    cntpairs += 1
                if (acti['asset']=='BTC' and actibal>0.00001):
                    cntpairs += 1
                elif (acti['asset']=='DOGE' and actibal>0.1):
                    cntpairs += 1
                elif (acti['asset']!='YFI' and acti['asset']!='DOGE' and acti['asset']!='BTC' and actibal>0.00001):
                    cntpairs += 1
            return cntpairs
        except:
            report_go('ERROR balance count')
            return 1
