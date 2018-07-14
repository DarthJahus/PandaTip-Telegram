#-*- coding: utf-8 -*-


import json
import codecs
import requests
from bs4 import BeautifulSoup, SoupStrainer
import re
import subprocess
from telegram.ext.dispatcher import run_async
from telegram.ext import Updater
from html import escape
from telegram.ext import CommandHandler
from telegram import ParseMode


# Constants
__wallet = "/usr/local/bin/pandacoind"


import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)


def commands(bot, update):
	user = update.message.from_user.username 
	bot.send_message(
		chat_id=update.message.chat_id,
		text="Initiating commands /tip & /withdraw have a specfic format,\n"
			"use them like so:\n \n Parameters: \n <user> = target user to tip \n"
			" <amount> = amount of pandacoin to utilise \n"
			" <address> = pandacoin address to withdraw to"
			" \n \n Tipping format: \n"
			" /tip <user> <amount> \n \n Withdrawing format: \n"
			" /withdraw <address> <amount>"
	)


def help(bot, update):
	bot.send_message(
		chat_id=update.message.chat_id,
		text="The following commands are at your disposal: /hi , /commands , /deposit , /tip , /withdraw , /price , /marketcap or /balance"
	)


def deposit(bot, update):
	chat_id = str(update.effective_chat.id)
	if update.effective_chat is None:
		_chat_type = "private"
	elif update.effective_chat.type == "private":
		_chat_type = "private"
	else:
		_chat_type = "group"
	# Only show deposit address if it's a private conversation with the bot
	if _chat_type == "private":
		_result = subprocess.run([__wallet, "getaccountaddress", chat_id], stdout=subprocess.PIPE)
		_address = (_result.stdout.strip()).decode("utf-8")
		update.message.reply_text(
			text="Your depositing address is: `%s`" % _address,
			quote=True,
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True
		)


# ToDo: Rewrite the whole logic; use tags instead of parsing usernames
# ToDo: Allow private tipping if the user can be tagged (@username available)
def tip(bot,update):
	user = update.message.from_user.username
	target = update.message.text[5:]
	amount = target.split(" ")[1]
	target = target.split(" ")[0]
	if user is None:
		bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
	else:
		machine = "@Pandacoin_bot"
		if target == machine:
			bot.send_message(chat_id=update.message.chat_id, text="HODL.")
		elif "@" in target:
			target = target[1:]
			user = update.message.from_user.username 
			core = "/usr/local/bin/pandacoind"
			result = subprocess.run([core,"getbalance",user],stdout=subprocess.PIPE)
			balance = float((result.stdout.strip()).decode("utf-8"))
			amount = float(amount)
			if balance < amount:
				bot.send_message(chat_id=update.message.chat_id, text="@{0} you have insufficent funds.".format(user))
			elif target == user:
				bot.send_message(chat_id=update.message.chat_id, text="You can't tip yourself silly.")
			else:
				balance = str(balance)
				amount = str(amount) 
				tx = subprocess.run([core,"move",user,target,amount],stdout=subprocess.PIPE)
				bot.send_message(chat_id=update.message.chat_id, text="@{0} tipped @{1} {2} PND".format(user, target, amount))
		else: 
			bot.send_message(chat_id=update.message.chat_id, text="Error that user is not applicable.")


# ToDo: Give balance only if a private chat
# ToDo: Remove WorldCoinIndex
def balance(bot,update):
	quote_page = requests.get('https://www.worldcoinindex.com/coin/pandacoin')
	strainer = SoupStrainer('div', attrs={'class': 'row mob-coin-table'})
	soup = BeautifulSoup(quote_page.content, 'html.parser', parse_only=strainer)
	name_box = soup.find('div', attrs={'class':'col-md-6 col-xs-6 coinprice'})
	name = name_box.text.replace("\n","")
	price = re.sub(r'\n\s*\n', r'\n\n', name.strip(), flags=re.M)
	price = re.sub("[^0-9^.]", "", price)
	price = float(price)
	user = update.message.from_user.username
	if user is None:
		bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
	else:
		core = "/usr/local/bin/pandacoind"
		result = subprocess.run([core,"getbalance",user],stdout=subprocess.PIPE)
		clean = (result.stdout.strip()).decode("utf-8")
		balance  = float(clean)
		fiat_balance = balance * price
		fiat_balance = str(round(fiat_balance,3))
		balance =  str(round(balance,3))
		bot.send_message(chat_id=update.message.chat_id, text="@{0} your current balance is: {1} PND ≈  ${2}".format(user,balance,fiat_balance))


def price(bot,update):
	quote_page = requests.get('https://www.worldcoinindex.com/coin/pandacoin')
	strainer = SoupStrainer('div', attrs={'class': 'row mob-coin-table'})
	soup = BeautifulSoup(quote_page.content, 'html.parser', parse_only=strainer)
	name_box = soup.find('div', attrs={'class':'col-md-6 col-xs-6 coinprice'})
	name = name_box.text.replace("\n","")
	price = re.sub(r'\n\s*\n', r'\n\n', name.strip(), flags=re.M)
	fiat = soup.find('span', attrs={'class': ''})
	kkz = fiat.text.replace("\n","")
	percent = re.sub(r'\n\s*\n', r'\n\n', kkz.strip(), flags=re.M)
	quote_page = requests.get('https://bittrex.com/api/v1.1/public/getticker?market=btc-rdd')
	soup = BeautifulSoup(quote_page.content, 'html.parser').text
	btc = soup[80:]
	sats = btc[:-2]
	bot.send_message(chat_id=update.message.chat_id, text="Pandacoin is valued at {0} Δ {1} ≈ {2}".format(price,percent,sats) + " ฿")


def withdraw(bot,update):
	user = update.message.from_user.username
	if user is None:
		bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
	else:
		target = update.message.text[9:]
		address = target[:35]
		address = ''.join(str(e) for e in address)
		target = target.replace(target[:35], '')
		amount = float(target)
		core = "/usr/local/bin/pandacoind"
		result = subprocess.run([core,"getbalance",user],stdout=subprocess.PIPE)
		clean = (result.stdout.strip()).decode("utf-8")
		balance = float(clean)
		if balance < amount:
			bot.send_message(chat_id=update.message.chat_id, text="@{0} you have insufficent funds.".format(user))
		else:
			amount = str(amount)
			tx = subprocess.run([core,"sendfrom",user,address,amount],stdout=subprocess.PIPE)
			bot.send_message(chat_id=update.message.chat_id, text="@{0} has successfully withdrew to address: {1} of {2} PND" .format(user,address,amount))


def hi(bot,update):
	user = update.message.from_user.username
	bot.send_message(chat_id=update.message.chat_id, text="Hello @{0}, how are you doing today?".format(user))


def moon(bot,update):
	bot.send_message(chat_id=update.message.chat_id, text="Moon mission inbound!")


def marketcap(bot,update):
	quote_page = requests.get('https://www.worldcoinindex.com/coin/pandacoin')
	strainer = SoupStrainer('div', attrs={'class': 'row mob-coin-table'})
	soup = BeautifulSoup(quote_page.content, 'html.parser', parse_only=strainer)
	name_box = soup.find('div', attrs={'class':'col-md-6 col-xs-6 coin-marketcap'})
	name = name_box.text.replace("\n","")
	mc = re.sub(r'\n\s*\n', r'\n\n', name.strip(), flags=re.M)
	bot.send_message(chat_id=update.message.chat_id, text="The current market cap of Pandacoin is valued at {0}".format(mc))


if __name__ == "__main__":
	updater = Updater(token='BOT_TOKEN')
	dispatcher = updater.dispatcher
	dispatcher.add_handler(CommandHandler('commands', commands))
	dispatcher.add_handler(CommandHandler('moon', moon))
	dispatcher.add_handler(CommandHandler('hi', hi))
	dispatcher.add_handler(CommandHandler('withdraw', withdraw))
	dispatcher.add_handler(CommandHandler('marketcap', marketcap))
	dispatcher.add_handler(CommandHandler('deposit', deposit))
	dispatcher.add_handler(CommandHandler('price', price))
	dispatcher.add_handler(CommandHandler('tip', tip))
	dispatcher.add_handler(CommandHandler('balance', balance))
	dispatcher.add_handler(CommandHandler('help', help))
	updater.start_polling()
