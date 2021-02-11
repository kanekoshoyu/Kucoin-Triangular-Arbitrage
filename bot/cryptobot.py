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
		'USD' : '0.000001',
		'BTC' : '0.00000001',
		'ETH' : '0.00000001',
		'VIDT' : '0.0001',
		'NANO' : '0.0001',
		'GO' : '0.0001',
		'BNB' : '0.0001',
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
        print('New Bot Setup with valid KuCoin Environment at ',self.init_time)

    def trade_code(self, coin_quote, coin_base):
        #sorting based on a table, ETH<BTC<USDT
        return coin_quote + '-' + coin_base

    # def price(self,coin_quote, coin_base, price_type):
    #     code = self.trade_code(coin_quote, coin_base)
    #     return Decimal(self.market.get_ticker(code)[price_type])

    def tick(self,coin_quote, coin_base):
        code = self.trade_code(coin_quote, coin_base)
        return self.market.get_ticker(code)

    def find_arbitrage(self, c: Circle):
        profit_near=Decimal('0')
        profit_far=Decimal('0')
        #take alt as comparator
        try:
            # Usual Trading, buy at bestBid, sell at bestAsk  
            # Faster trading, lower profit: buy at bestAsk, sell at bestBid
            altbase = self.tick(c.alt, c.base)
            altmid = self.tick(c.alt, c.mid)
            midbase = self.tick(c.mid, c.base)

            alt_buy = Decimal(altmid['price']) * Decimal(midbase['price'])
            alt_sell = Decimal(altbase['bestBid']) 
            profit_far = (alt_sell-alt_buy)/alt_buy * Decimal('100')
            alt_buy = Decimal(altbase['price']) 
            alt_sell = Decimal(altmid['bestBid']) * Decimal(midbase['price']) 
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
        # print(c.alt, c.action, c.profit)

    def best_circle(self):
        #first find the biggest opportunity
        print('Sorting the best opportunity...')
        best_circle = self.circles[0]
        for circle in self.circles:
            self.find_arbitrage(circle)
            if circle.profit>best_circle.profit:
                best_circle = circle
        return best_circle

    def feed_coins(self, coins):
        for coin in coins:
            self.circles.append(Circle(coin))
            
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
            price = Decimal(self.market.get_ticker(code)[price_type])
            if command == 'buy':
                try:
                    available_base = Decimal(self.user.get_transferable(coin_base,'TRADE')['available'])*Decimal('0.95')
                    # print('available_base', coin_base, available_base)
                    amount_quote = self.round_by_increment(available_base/price, increment_quote)
                except Exception as e:
                    print("Account fail", e)
            elif command == 'sell':
                try:
                    avaliable_quote = Decimal(self.user.get_transferable(coin_quote,'TRADE')['available'])*Decimal('0.95')
                    amount_quote = self.round_by_increment(avaliable_quote, increment_quote)
                    # print('avaliable_quote', avaliable_quote)
                except Exception as e:
                    print("Account fail", e)
            else:
                print('invalid command',command)
        except Exception as e:
            print("Ticker fail", e)
            
        print('amount_quote', amount_quote)
        if (amount_quote > Decimal(minSize[coin_quote])):
            print(code, command, amount_quote, price)
            try:
                order_id = self.trade.create_limit_order(code, command, str(amount_quote), str(price))
                print(command, "order success", order_id)
            except Exception as e:
                print(command, "order fail", e)
        else:
            if (amount_quote == Decimal('0.0')):
                print('coin balance not available')
            else:
                print('coin balance insufficient')

    def serial_trade(self, circle):
        #default: buy_near
        print('serial trade')
        #try sell at bestBid for not holpding alts too long
        if circle.action == Action.buy_far:
            self.single_trade(circle.mid, circle.base, 'buy', 'price')
            self.single_trade(circle.alt, circle.mid, 'buy', 'price')
            self.single_trade(circle.alt, circle.base, 'sell', 'bestBid')
        elif circle.action ==Action.buy_near:
            self.single_trade(circle.alt, circle.base, 'buy', 'price')
            self.single_trade(circle.alt, circle.mid, 'sell', 'bestBid')
            self.single_trade(circle.mid, circle.base, 'sell', 'price')

    def run(self):
        threshold=Decimal('0.31')
        while True:
            best_circle = self.best_circle()
            if best_circle.action != Action.wait and best_circle.profit>threshold:
                print(best_circle.action, best_circle.alt, best_circle.profit)
                self.serial_trade(best_circle)
            else:
                print('skip', best_circle.alt, best_circle.profit)
            # print('\r\n')

#run

# coins = ['VIDT','NANO','GO', 'ETH']
print('Crypto Bot')
coins = ['VIDT','GO', 'BNB', 'NANO']
bot = Bot()
bot.feed_coins(coins)
bot.run()