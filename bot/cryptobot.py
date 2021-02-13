from kucoin.client import User, Market, Trade
from datetime import datetime
import time, enum
from decimal import Decimal

api_key = '6012f5afbd074e0006b769ba'
api_secret = '07d14b4f-b8ea-4adb-99f2-dd65d302e0bd'
api_passphrase = 'passphrase'

minSize = {
		'USD' : '0.01',
		'BTC' : '0.00001',
		'ETH' : '0.00001',
		'VIDT' : '0.1',
		'NANO' : '0.1',#not sure
		'GO' : '1',
		'BNB' : '0.001',#not sure
	}

increment = {
		'USD' : '0.01',
		'BTC' : '0.00001',
		'ETH' : '0.00001',
		'VIDT' : '0.01',
		'NANO' : '0.001',
		'GO' : '1',
		'BNB' : '0.001',
	}

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
    mid='BTC'
    base='USDT'
    profit = Decimal('0')
    # alt=''

    def __init__(self, alt_coin):
        self.alt=alt_coin
        self.action=Action.wait
        print(alt_coin,' Circle Setup')
    
    def balance(self):
        # kucoin.user.get_withdrawal_quota(alt)
        #KuCoinApi.user
        print('')

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
        print('New Bot Setup with valid KuCoin Environment at',self.init_time)

    def trade_code(self, coin_quote, coin_base):
        #sorting based on a table, ETH<BTC<USDT
        return coin_quote + '-' + coin_base

    def tick(self,coin_quote, coin_base):
        code = self.trade_code(coin_quote, coin_base)
        return self.market.get_ticker(code)

    def mean(self, price_order: str, price_mean: str):
        return ( Decimal(price_order) + Decimal(price_mean) ) / Decimal('2.0')

    def find_arbitrage(self, c: Circle):
        profit_near=Decimal('0')
        profit_far=Decimal('0')
        try:
            # Usual Trading, buy at bestBid, sell at bestAsk  
            # Faster trading, lower profit: buy at bestAsk, sell at bestBid
            altbase = self.tick(c.alt, c.base)
            altmid = self.tick(c.alt, c.mid)
            midbase = self.tick(c.mid, c.base)

            # alt_buy = Decimal(altmid['price']) * Decimal(midbase['price'])
            # alt_sell = Decimal(altbase['bestBid']) 
            alt_buy     = self.mean(altmid['bestAsk'], altmid['price']) * self.mean(midbase['bestAsk'], midbase['price'])
            alt_sell    = self.mean(altbase['bestBid'], altbase['price'])
            profit_far  = (alt_sell-alt_buy)/alt_buy * Decimal('100')
            # alt_buy = Decimal(altbase['price']) 
            # alt_sell = Decimal(altmid['bestBid']) * Decimal(midbase['price'])
            alt_buy     = self.mean(altbase['bestAsk'], altbase['price'])
            alt_sell    = self.mean(altmid['bestBid'], altmid['price']) * self.mean(midbase['bestBid'], midbase['price'])
            profit_near = (alt_sell-alt_buy)/alt_buy * Decimal('100')
        except Exception as e:
            print('Quote Fail')
            print(e)
        if profit_far>profit_near and profit_far>Decimal('0'):
            c.profit = profit_far
            c.action = Action.buy_far
        elif profit_near>profit_far and profit_near>Decimal('0'):
            c.profit = profit_near
            c.action = Action.buy_near
        else:
            c.profit = Decimal('0')
            c.action = Action.wait
        # print(c.alt, c.action, round(float(c.profit), 4), '%')

    def best_circle(self):
        #first find the biggest opportunity
        print('Sorting the best circle...')
        best_circle = self.circles[0]
        for c in self.circles:
            self.find_arbitrage(c)
            if c.profit>best_circle.profit:
                best_circle = c
        return best_circle

    def feed_coins(self, coins):
        for coin in coins:
            self.circles.append(Circle(coin))
        print('')
            
    def round_by_increment(self, amount_dec, increment_dec):
        mul = Decimal(round(amount_dec/increment_dec))
        ans = mul*increment_dec
        return ans

    def single_trade(self, coin_quote, coin_base, command, price_type):
        #hi: quote, lo: base
        increment_quote = Decimal(increment[coin_quote])
        code = self.trade_code(coin_quote, coin_base)
        amount_quote = Decimal('0.0') # Default only when connection error
        try:
            quotebase = self.market.get_ticker(code)
            price = self.mean(quotebase[price_type], quotebase['price'])
        except Exception as e:
            print("Ticker fail", e)
            price = Decimal('0')

        try:
            if command == 'buy':
                available_base = Decimal(self.user.get_transferable(coin_base,'TRADE')['available'])
                amount_quote = self.round_by_increment(available_base/price, increment_quote)
                print('increment is',increment_quote)

            elif command == 'sell':
                avaliable_quote = Decimal(self.user.get_transferable(coin_quote,'TRADE')['available'])
                amount_quote = self.round_by_increment(avaliable_quote, increment_quote)
            else:
                print('invalid command',command)
        except Exception as e:
                print("Account fail", e)

        if (amount_quote >= Decimal(minSize[coin_quote])):
            print(command, code, amount_quote,' at ', ｐrice)
            try:
                order_id = self.trade.create_limit_order(code, command, str(amount_quote), str(price))
                print(command, "order success", order_id, '\r\n')
            except Exception as e:
                print(command, "order fail", e, '\r\n')
        else:
            print('balance insufficient', amount_quote)

    def serial_trade(self, circle):
        #default: buy_near
        print('serial trade')
        #try sell at bestBid for not holpding alts too long
        if circle.action == Action.buy_far:
            self.single_trade(circle.mid, circle.base, 'buy', 'bestAsk')
            # Setup cancel order mechanism
            self.single_trade(circle.alt, circle.mid, 'buy', 'bestAsk')
            self.single_trade(circle.alt, circle.base, 'sell', 'bestBid')
        elif circle.action ==Action.buy_near:
            self.single_trade(circle.alt, circle.base, 'buy', 'bestAsk')
            self.single_trade(circle.alt, circle.mid, 'sell', 'bestBid')
            self.single_trade(circle.mid, circle.base, 'sell', 'bestBid')

    def run(self):
        threshold=Decimal('0.3')
        while True:
            best_circle = self.best_circle()
            if best_circle.action != Action.wait and best_circle.profit>threshold:
                print(best_circle.action, best_circle.alt, best_circle.profit)
                self.serial_trade(best_circle)
            else:
                print('skip', best_circle.alt, round(float(best_circle.profit), 4),'%')

# coins = ['VIDT','NANO','GO', 'ETH']
print('Crypto Bot')
coins = ['VIDT','GO', 'BNB', 'NANO']
bot = Bot()
bot.feed_coins(coins)
bot.run()