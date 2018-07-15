#!/usr/bin/python
#coding=utf-8


import requests
from bs4 import BeautifulSoup, SoupStrainer
import re
import subprocess
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram import ParseMode
from PandaRPC import PandaRPC, Wrapper as RPCWrapper
from HelperFunctions import *
import logging
logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO
)

config = load_file_json("config.json")
_lang = "en" # ToDo: Per-user language
strings = Strings("strings.json")


# Constants
__wallet_rpc = RPCWrapper(PandaRPC(config["rpc-uri"], (config["rpc-user"], config["rpc-psw"])))


# ToDo: Don't forget to write the strings in strings.json (they are actually empty)
def cmd_start(bot, update, args):
	"""Reacts when /start is sent to the bot."""
	if update.effective_chat.type == "private":
		# Check for deep link
		if len(args) > 0:
			if args[0].lower() == "about":
				cmd_about(bot, update)
			elif args[0].lower() == "help":
				cmd_help(bot, update)
			else:
				update.message.reply_text(
					strings.get("error_bad_deep_link", _lang),
					quote=True,
					parse_mode=ParseMode.MARKDOWN,
					disable_web_page_preview=True
				)
		else:
			update.message.reply_text(
				strings.get("welcome", _lang),
				quote=True,
				parse_mode=ParseMode.MARKDOWN,
				disable_web_page_preview=True
			)


def cmd_about(bot, update):
	if update.effective_chat is None:
		_chat_type = "private"
	elif update.effective_chat.type == "private":
		_chat_type = "private"
	else:
		_chat_type = "group"
	#
	if _chat_type == "private":
		# Check if callback
		try:
			if update.callback_query.data is not None:
				update.callback_query.answer(strings.get("about", _lang))
		except:
			pass
		bot.send_message(
			chat_id=update.effective_chat.id,
			text=strings.get("about", _lang),
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True
		)
	else:
		update.message.reply_text(
			"%s\n[deeplink](https://telegram.me/%s?start=about)" % (strings.get("about_public", _lang), config["bot_name"]),
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True
		)
	return True


def cmd_help(bot, update):
	if update.effective_chat is None:
		_chat_type = "private"
	elif update.effective_chat.type == "private":
		_chat_type = "private"
	else:
		_chat_type = "group"
	#
	if _chat_type == "private":
		# Check if callback
		try:
			if update.callback_query.data is not None:
				update.callback_query.answer(strings.get("help", _lang))
		except:
			pass
		bot.send_message(
			chat_id=update.effective_chat.id,
			text=strings.get("help", _lang),
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True
		)
	else:
		update.message.reply_text(
			"%s\n[deeplink](https://telegram.me/%s?start=help)" % (strings.get("help_public", _lang), config["bot_name"]),
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True
		)
	return True


def deposit(bot, update):
	"""
	This commands works only in private.
	If the user has no address, a new account is created with his Telegram user ID (str)
	"""
	if update.effective_chat is None:
		_chat_type = "private"
	elif update.effective_chat.type == "private":
		_chat_type = "private"
	else:
		_chat_type = "group"
	# Only show deposit address if it's a private conversation with the bot
	if _chat_type == "private":
		chat_id = str(update.effective_chat.id)
		# _result = subprocess.run([__wallet, "getaccountaddress", chat_id], stdout=subprocess.PIPE)
		_rpc_call = __wallet_rpc.getaccountaddress(chat_id)
		if not _rpc_call["success"]:
			print("Error during RPC call.")
		else:
			if _rpc_call["result"]["error"] is not None:
				print("Error: %s" % _rpc_call["result"]["error"])
			else:
				_address = json.dumps(_rpc_call["result"]["result"])
				update.message.reply_text(
					text="Your deposit address is: `%s`" % _address,
					quote=True,
					parse_mode=ParseMode.MARKDOWN,
					disable_web_page_preview=True
				)



# Done: Give balance only if a private chat (2018-07-15)
# Done: Remove WorldCoinIndex (2018-07-15)
# ToDo: Add conversion
def balance(bot,update):
	if update.effective_chat is None:
		_chat_type = "private"
	elif update.effective_chat.type == "private":
		_chat_type = "private"
	else:
		_chat_type = "group"
	# Only show balance if it's a private conversation with the bot
	if _chat_type == "private":
		chat_id = str(update.effective_chat.id)
		# get address of user
		_rpc_call = __wallet_rpc.getaddress(chat_id)
		if not _rpc_call["success"]:
			print("Error during RPC call.")
		elif _rpc_call["result"]["error"] is not None:
			print("Error: %s" % _rpc_call["result"]["error"])
		else:
			_address = json.dumps(_rpc_call["result"]["result"])
			_rpc_call = __wallet_rpc.getbalance(_address)
			if not _rpc_call["success"]:
				print("Error during RPC call.")
			elif _rpc_call["result"]["error"] is not None:
				print("Error: %s" % _rpc_call["result"]["error"])
			else:
				_balance = float(json.dumps(_rpc_call["result"]["result"]))
				update.message.reply_text(
					text="Your balance is: `%.0f PND`" % _balance
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
	updater = Updater(token=config["telegram-token"])
	dispatcher = updater.dispatcher
	# TGBot commands
	dispatcher.add_handler(CommandHandler('start', cmd_start, pass_args=True))
	dispatcher.add_handler(CommandHandler('help', cmd_help))
	dispatcher.add_handler(CommandHandler('about', cmd_about))
	# Funny commands
	dispatcher.add_handler(CommandHandler('moon', moon))
	dispatcher.add_handler(CommandHandler('hi', hi))
	# Tipbot commands
	dispatcher.add_handler(CommandHandler('tip', tip))
	dispatcher.add_handler(CommandHandler('withdraw', withdraw))
	dispatcher.add_handler(CommandHandler('deposit', deposit))
	dispatcher.add_handler(CommandHandler('address', deposit)) # alias for /deposit
	dispatcher.add_handler(CommandHandler('balance', balance))
	# Conversion commands
	dispatcher.add_handler(CommandHandler('marketcap', marketcap))
	dispatcher.add_handler(CommandHandler('price', price))
	updater.start_polling()
