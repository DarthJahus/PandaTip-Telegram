#!/usr/bin/python
#coding=utf-8


import requests
import re
import subprocess
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.error import BadRequest
from telegram import ParseMode
from PandaRPC import PandaRPC, Wrapper as RPCWrapper
from HelperFunctions import *
import sys, traceback
import logging
logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO
)

config = load_file_json("config.json")
_lang = "fr" # ToDo: Per-user language
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
		# ToDo: Button
		update.message.reply_text(
			"%s\n[About %s](https://telegram.me/%s?start=about)" % (
				strings.get("about_public", _lang), config["telegram-botname"], config["telegram-botname"]
			),
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
		# ToDo: Button
		update.message.reply_text(
			"%s\n[Help!](https://telegram.me/%s?start=help)" % (strings.get("help_public", _lang), config["telegram-botname"]),
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
		_user_id = '@' + update.effective_user.username.lower()
		if _user_id is None: _user_id = str(update.effective_user.id)
		# _result = subprocess.run([__wallet, "getaccountaddress", chat_id], stdout=subprocess.PIPE)
		_rpc_call = __wallet_rpc.getaccountaddress(_user_id)
		if not _rpc_call["success"]:
			print("Error during RPC call.")
		else:
			if _rpc_call["result"]["error"] is not None:
				print("Error: %s" % _rpc_call["result"]["error"])
			else:
				_address = _rpc_call["result"]["result"]
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
		# See issue "USERNAME1"
		_user_id = '@' + update.effective_user.username.lower()
		if _user_id is None: _user_id = str(update.effective_user.id)
		# get address of user
		_rpc_call = __wallet_rpc.getaccountaddress(_user_id)
		if not _rpc_call["success"]:
			if _rpc_call["message"] == 404:
				update.message.reply_text(
					text="You seem to be a new user.\nIf you want to create an account, please use the command /address",
					quote=True
				)
			else:
				print("Error during RPC call: %s" % _rpc_call["message"])
		elif _rpc_call["result"]["error"] is not None:
			print("Error: %s" % _rpc_call["result"]["error"])
		else:
			_address = _rpc_call["result"]["result"]
			_rpc_call = __wallet_rpc.getbalance(_address)
			if not _rpc_call["success"]:
				print("Error during RPC call.")
			elif _rpc_call["result"]["error"] is not None:
				print("Error: %s" % _rpc_call["result"]["error"])
			else:
				_balance = float(_rpc_call["result"]["result"])
				update.message.reply_text(
					text="Your balance is: `%.0f PND`" % _balance,
					parse_mode=ParseMode.MARKDOWN,
					quote=True
				)


# Done: Rewrite the whole logic; use tags instead of parsing usernames (2018-07-15)
# ToDo: Allow private tipping if the user can be tagged (@username available) (Probably works, now)
def tip(bot,update):
	# /tip <user> <amount>
	_message = update.effective_message.text
	_modifier = 0
	_recipients = {}
	for entity in update.effective_message.entities:
		if entity.type == "text_mention":
			# UserId is unique
			_username = entity.user.name
			if str(entity.user.id) not in _recipients:
				_recipients[str(entity.user.id)] = (_username, entity.offset, entity.length)
		elif entity.type == "mention":
			# _username starts with @
			# _username is unique
			_username = update.effective_message.text[entity.offset:(entity.offset+entity.length)]
			if _username not in _recipients:
				_recipients[_username] = (_username, entity.offset, entity.length)
		_part = _message[:entity.offset-_modifier]
		_message = _message[:entity.offset-_modifier] + _message[entity.offset+entity.length-_modifier:]
		_modifier = entity.offset+entity.length-len(_part)
	print(_recipients)
	_amounts = _message.split()
	# check if amounts are all convertible to float
	_amounts_float = []
	try:
		for _amount in _amounts:
			_amounts_float.append(float(_amount))
	except:
		_amounts_float = []
	if len(_amounts_float) != len(_recipients):
		update.message.reply_text(
			text="There was an error in your tip. Number of recipients needs to be the same as the number of amounts.",
			quote=True
		)
	else:
		# now check if user has enough balance
		_user_id = '@' + update.effective_user.username.lower()
		if _user_id is None: _user_id = str(update.effective_user.id)
		# get address of user
		_rpc_call = __wallet_rpc.getaccountaddress(_user_id)
		if not _rpc_call["success"]:
			if _rpc_call["message"] == 404:
				update.message.reply_text(
					text="You seem to be a new user.\nIf you want to create an account, please use the command /address",
					quote=True
				)
			else:
				print("Error during RPC call: %s" % _rpc_call["message"])
		elif _rpc_call["result"]["error"] is not None:
			print("Error: %s" % _rpc_call["result"]["error"])
		else:
			_address = _rpc_call["result"]["result"]
			_rpc_call = __wallet_rpc.getbalance(_address)
			if not _rpc_call["success"]:
				print("Error during RPC call.")
			elif _rpc_call["result"]["error"] is not None:
				print("Error: %s" % _rpc_call["result"]["error"])
			else:
				_balance = float(_rpc_call["result"]["result"])
				# Now, finally, check if user has enough funds
				if sum(_amounts_float) > _balance:
					update.message.reply_text(
						text="Sorry, you don't have enough funds for this operation.\nYou need `%.4f PND`" % sum(_amounts_float),
						quote=True
					)
				else:
					# Now tip
					i = 0
					for _recipient in _recipients:
						if _recipient[0] == '@':
							# ToDo: Get the id (actually not possible (Bot API 3.6, Feb. 2018)
							# Using the @username
							# ToDo: When requesting a new address, if user has a @username, then use that username
							# Problem: If someone has no username, then later creates one, he loses access to his account
							# ToDo: Create a /scavenge command that allows people who had UserID to migrate to UserName
							_recipient_id = _recipient
						else:
							_recipient_id = _recipient
						_rpc_call = __wallet_rpc.move(_user_id, _recipient_id, _amounts_float[i])
						i += 1
						if not _rpc_call["success"]:
							print("Error during RPC call.")
						elif _rpc_call["result"]["error"] is not None:
							print("Error: %s" % _rpc_call["result"]["error"])
						else:
							print(
								"%s successfully tipped %s with `%.4f PND`" % (
									update.effective_user.name, _recipients[_recipient][0], _amounts_float[i]
								)
							)


# PMh8nM5gCza8fAtwi5VWpBMQeu53MrQe9r
def price(bot,update):
	# ToDo:
	pass


# ToDo: Revamp withdraw() function
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


def scavenge(bot, update):
	if update.effective_chat is None:
		_chat_type = "private"
	elif update.effective_chat.type == "private":
		_chat_type = "private"
	else:
		_chat_type = "group"
	# Only if it's a private conversation with the bot
	if _chat_type == "private":
		_username = '@' + update.effective_user.username.lower()
		if _username is None:
			update.message.reply_text(
				text="Sorry, this command is not for you.",
				quote=True
			)
		else:
			_user_id = str(update.effective_user.id)
			# Done: Check balance of UserID (2018-07-16)
			# get address of user
			_rpc_call = __wallet_rpc.getaccountaddress(_user_id)
			if not _rpc_call["success"]:
				if _rpc_call["message"] == 404:
					update.message.reply_text(
						text="You had no previous balance stored with your user id (`%s`)." % _user_id,
						parse_mode=ParseMode.MARKDOWN,
						quote=True
					)
				else:
					print("Error during RPC call: %s" % _rpc_call["message"])
			elif _rpc_call["result"]["error"] is not None:
				print("Error: %s" % _rpc_call["result"]["error"])
			else:
				_address = _rpc_call["result"]["result"]
				_rpc_call = __wallet_rpc.getbalance(_address)
				if not _rpc_call["success"]:
					print("Error during RPC call.")
				elif _rpc_call["result"]["error"] is not None:
					print("Error: %s" % _rpc_call["result"]["error"])
				else:
					_balance = float(_rpc_call["result"]["result"])
					# ToDo: Move balance from UserID to @username if balance > 0
					if _balance == 0:
						update.message.reply_text(
							text="Your previous account (`%s`) is empty. Nothing to scavenge." % _user_id,
							parse_mode=ParseMode.MARKDOWN,
							quote=True
						)
					else:
						# Move the funds from UserID to Username
						_rpc_call = __wallet_rpc.move(_user_id, _username, _balance)
						if not _rpc_call["success"]:
							print("Error during RPC call.")
						elif _rpc_call["result"]["error"] is not None:
							print("Error: %s" % _rpc_call["result"]["error"])
						else:
							update.message.reply_text(
								text="Successfully scavenged `%.4f PND` from your previous account (`%s`)" % (_balance, _user_id),
								parse_mode=ParseMode.MARKDOWN,
								quote=True
							)


# ToDo: Take tx fee into account


def hi(bot,update):
	user = update.message.from_user.username
	bot.send_message(chat_id=update.message.chat_id, text="Hello @{0}, how are you doing today?".format(user))


def moon(bot,update):
	bot.send_message(chat_id=update.message.chat_id, text="Moon mission inbound!")


def marketcap(bot,update):
	# ToDo:
	pass


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
	dispatcher.add_handler(CommandHandler("scavenge", scavenge))
	# Conversion commands
	dispatcher.add_handler(CommandHandler('marketcap', marketcap))
	dispatcher.add_handler(CommandHandler('price', price))
	updater.start_polling()
