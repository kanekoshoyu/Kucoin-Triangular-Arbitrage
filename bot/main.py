from cryptobot import Bot
import time

print("Crypto App")
coins = ['VIDT','NANO','GO','ETH']

bot = Bot()
bot.feed_coins(coins)
bot.run()

#ToDo for next generation: faster quotation by Socket

# nmcli con mod VPNNAME vpn.secrets 'form:main:username=USERNAME','save_passwords=yes'
