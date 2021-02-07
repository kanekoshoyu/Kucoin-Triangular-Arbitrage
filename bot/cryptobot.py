from kucoin.client import User, Market, Trade
from datetime import datetime
import time, enum

api_key = '6012f5afbd074e0006b769ba'
api_secret = '07d14b4f-b8ea-4adb-99f2-dd65d302e0bd'
api_passphrase = 'passphrase'

# class KuCoinApi(object):
#     user=None
#     market=None
#     trade=None
#     try:
#         user = User(api_key, api_secret, api_passphrase)
#         market = Market(url='https://api.kucoin.com')
#         trade = Trade(key=api_key, secret=api_secret, passphrase=api_passphrase, is_sandbox=False, url='')
#         print('KuCoin Environment Setup')
#     except Exception as e:
#         print('KuCoin Environment Fail')
#         print(e)

class TransactionRecord(object):
    id=None
    buy=None
    def __init__(self, coin_sold, coin_bought, price):
        self.price=price
        self.coin_bought=coin_bought
        self.coin_sold=coin_sold
        self.time = datetime.now()
        print('New Transaction Setup')

    def report(self):
        print('sold ',self.coin_sold,',  bought ',self.coin_bought,' at ',self.price,', in ',self.time)

class Action(enum.Enum):
    wait = 0
    buy_near = 1
    buy_far = 2

class Circle(object):
    top='BTC'
    base='USDT'
    far_counter=0.0
    near_counter=0.0
    diff = 0.0
    # alt=''
    
    def __init__(self, alt_coin):
        self.alt=alt_coin
        self.action=Action.wait
        print(alt_coin,' Circle Setup')
    
    def balance(self):
        # kucoin.user.get_withdrawal_quota(alt)
        #KuCoinApi.user
        print('')


#Try with only 2 cycles first
class Bot(object):
    circles = []
    def __init__(self):
        self.init_time = datetime.now()
        try:
            self.user = User(api_key, api_secret, api_passphrase)
            self.market = Market(url='https://api.kucoin.com')
            self.trade = Trade(key=api_key, secret=api_secret, passphrase=api_passphrase, is_sandbox=False)
            print('KuCoin Environment Setup')
        except Exception as e:
            print('KuCoin Environment Fail')
            print(e)

        # self.kucoin = KuCoinApi()
        print('New Bot Setup with valid KuCoin Environment at ',self.init_time)

    def trade_code(self, coin_hi, coin_lo):
        #sorting based on a table, ETH<BTC<USDT
        return coin_hi + '-' + coin_lo

    def mean_price(self,coin_hi, coin_lo):
        code = self.trade_code(coin_hi, coin_lo)
        ticker = self.market.get_ticker(code)
        bestAsk = float(ticker['bestAsk'])
        bestBid = float(ticker['bestBid'])
        mean = (bestAsk+bestBid)/2.0    #Last updated minute
        return mean
    
    def find_arbitrage(self, circle):
        threshold=0.3
        #take alt as comparator
        try:
            alt_fp = self.mean_price(circle.alt, circle.top) * self.mean_price(circle.top, circle.base)
            alt_np = self.mean_price(circle.alt, circle.base)
        except Exception as e:
            print('Quote Fail')
            print(e)
            alt_fp=1.0
            alt_np=1.0
        #print('far:',alt_fp)
        #print('near:',alt_np)
        circle.diff = (alt_fp-alt_np)/alt_fp*100
        if circle.diff>threshold:
            # print('near is cheaper by ',diff,'%')
            circle.action = Action.buy_near
        elif abs(circle.diff)>threshold:
            # print('far is cheaper by ',diff,'%') 
            circle.action = Action.buy_far
        else:
            # print('only',diff,'%, wait')
            circle.action = Action.wait

    def best_circle(self):
        #first find the biggest opportunity
        print('Sorting the best opportunity...')
        best_circle = self.circles[0]
        for circle in self.circles:
            print(circle.alt)
            self.find_arbitrage(circle)
            if abs(circle.diff)>abs(best_circle.diff):
                best_circle = circle
        return best_circle

    def feed_coins(self, coins):
        for coin in coins:
            self.circles.append(Circle(coin))

    def single_trade(self, coin_hi, coin_lo, command):
        code = self.trade_code(coin_hi, coin_lo)
        if command == 'buy':
            price = float(self.market.get_ticker(code)['price'])
            # price_hi = float(tick['bestAsk'])#Lowest Sold
            # price_lo = float(tick['bestBid'])#Highest Bought
            amount_lo = float(self.user.get_transferable(coin_lo,'TRADE')['available'])
            amount_hi = amount_lo/price
            if (amount_lo == 0.0):
                print('fund not available')
            else:
                print(code, command, amount_hi, price, amount_lo)
                try:
                    order_id = self.trade.create_limit_order(code, command, amount_hi, price)
                    print("Buy order success", order_id)
                except Exception as e:
                    print("Buy order fail", e)
        elif command == 'sell':
            price = float(self.market.get_ticker(code)['price'])
            # price_hi = float(self.market.get_ticker(code)['bestAsk'])#Lowest Sold
            # price_lo = float(self.market.get_ticker(code)['bestBid'])#Highest Bought
            amount_hi = float(self.user.get_transferable(coin_hi,'TRADE')['available'])
            amount_lo = amount_hi*price
            if (amount_hi == 0.0):
                print('fund not available')
            else:
                print(code, command, amount_hi, price, amount_lo)
                try:
                    order_id = self.trade.create_limit_order(code, command, amount_lo, price)
                    print("Sell order success", order_id)
                except Exception as e:
                    print("Sell order fail", e)
        else:
            print('invalid command',command)



    def serial_trade(self, circle):
        #default: buy_near
        print('serial trade')
        if circle.action == Action.buy_far:
            self.single_trade(circle.top, circle.base, 'buy')
            self.single_trade(circle.alt, circle.top, 'buy')
            self.single_trade(circle.alt, circle.base, 'sell')
        elif circle.action ==Action.buy_near:
            self.single_trade(circle.alt, circle.base, 'buy')
            self.single_trade(circle.alt, circle.top, 'sell')
            self.single_trade(circle.top, circle.base, 'sell')

    def run(self):
        while True:
            best_circle = self.best_circle()
            if best_circle.action != Action.wait:
                print('trade',best_circle.alt, best_circle.diff)
                self.serial_trade(best_circle)
            else:
                print('skip', best_circle.alt, best_circle.diff)
            print('\r\n')

#run
print('Crypto Bot')
coins = ['VIDT','NANO','GO','ETH']

bot = Bot()
bot.feed_coins(coins)
bot.run()