from kucoin.client import User, Market, Trade
from datetime import datetime
import time


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

class Circle(object):
    top='BTC'
    base='USDT'
    far_counter=0.0
    near_counter=0.0
    # alt=''
    
    def __init__(self, alt_coin):
        self.alt=alt_coin
        self.opportunity_flag=False
        print(alt_coin,' Circle Setup')
    
    def balance(self):
        # kucoin.user.get_withdrawal_quota(alt)
        #KuCoinApi.user
        print("")


    def place_order(self):
        #kucoin.
        print("")
        # kucoin.trade.create_limit_order()


#Try with only 2 cycles first
class Bot(object):

    def __init__(self):
        self.init_time = datetime.now()
        try:
            self.user = User(api_key, api_secret, api_passphrase)
            self.market = Market(url='https://api.kucoin.com')
            self.trade = Trade(key=api_key, secret=api_secret, passphrase=api_passphrase, is_sandbox=False, url='')
            print('KuCoin Environment Setup')
        except Exception as e:
            print('KuCoin Environment Fail')
            print(e)

        # self.kucoin = KuCoinApi()
        print("New Bot Setup with valid KuCoin Environment at ",self.init_time)

    def trade_code(self, coin_top, coin_low):
        #sorting based on a table
        #ETH<BTC<USDT
        return coin_top + "-" + coin_low

    def mean_price(self,coin_hi, coin_lo):
        code = self.trade_code(coin_hi, coin_lo)
        ticker = self.market.get_ticker(code)
        bestAsk = float(ticker['bestAsk'])
        bestBid = float(ticker['bestBid'])
        mean = (bestAsk+bestBid)/2.0    #Last updated minute
        # qll = (q[-1][2]+q[-1][3])/2   #second last updated minute
        # print(code,": ",code)
        #make quotation and calculate the latest price with the engine
        return mean
    
    def try_quote(self):
        coin = self.mean_price('BTC', 'USDT')
        print(coin)

    
    def find_arbitrage(self, circle):
        #take alt as comparator
        try:
            alt_fp = self.mean_price(circle.alt, circle.top) * self.mean_price(circle.top, circle.base)
            alt_np = self.mean_price(circle.alt, circle.base)
        except Exception as e:
            print('Quote Fail')
            print(e)
            alt_fp=1.0
            alt_np=1.0
        # print("far:",alt_fp)
        # print("near:",alt_np)
        diff = 0.0
        if (alt_np<alt_fp):
            diff=(alt_fp-alt_np)/alt_fp*100
            print("near is cheaper by ",diff,"%")
            circle.far_counter+=diff
        else:
            diff = (alt_np-alt_fp)/alt_np*100
            print("far is cheaper by ",diff,"%") 
            circle.near_counter+=diff

        if diff > 0.4:
            circle.opportunity_flag=True

    def run(self):
        circles = [Circle('ETH'), Circle('GO')]#highly volatile!
        circles = [Circle('VIDT')]

        # alt_base = self.trade_code(alt[0], base)
        # alt_mid =  self.trade_code(alt[1], base)
        # mid_base =  self.trade_code(alt[0], alt[1])

        while True:
            for circle in circles:
                print(circle.alt)
                self.find_arbitrage(circle)
                if circle.opportunity_flag:
                    circle.opportunity_flag=False
                    print("Opportunity found!")
                    #Trade here
                    circle.place_order()
                # print('near: ',circle.near_counter,'far: ',circle.far_counter)

#run
print("Crypto Bot")
bot = Bot()
bot.run()
bot.try_quote()