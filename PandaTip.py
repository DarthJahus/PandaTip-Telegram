#!/usr/bin/python
#coding=utf-8


import emoji
from telegram.ext import Updater
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from PandaRPC import PandaRPC, Wrapper as RPCWrapper
from HelperFunctions import *
import logging
logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO
)
import time
from datetime import datetime


config = load_file_json("config.json")
_lang = "en" # ToDo: Per-user language
strings = Strings("strings.json")
_paused = False
_spam_filter = AntiSpamFilter(config["spam_filter"][0], config["spam_filter"][1])

# Constants
__wallet_rpc = RPCWrapper(PandaRPC(config["rpc-uri"], (config["rpc-user"], config["rpc-psw"])))


# ToDo: Add service commands like /pause (pauses the bot for everyone), and maybe some commands to check the health of the daemon / wallet.


# ToDo: Don't forget to write the strings in strings.json (they are actually empty)
def cmd_start(bot, update, args):
	"""Reacts when /start is sent to the bot."""
	if update.effective_chat.type == "private":
		if not _spam_filter.verify(str(update.effective_user.id)):
			return
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
			_button_help = InlineKeyboardButton(
				text=emoji.emojize(strings.get("button_help", _lang), use_aliases=True),
				callback_data="help"
			)
			_button_about = InlineKeyboardButton(
				text=emoji.emojize(strings.get("button_about", _lang), use_aliases=True),
				callback_data="about"
			)
			_markup = InlineKeyboardMarkup(
				[
					[_button_help, _button_about]
				]
			)
			update.message.reply_text(
				emoji.emojize(strings.get("welcome", _lang), use_aliases=True),
				quote=True,
				parse_mode=ParseMode.MARKDOWN,
				disable_web_page_preview=True,
				reply_markup=_markup
			)


def cmd_about(bot, update):
	if not _spam_filter.verify(str(update.effective_user.id)):
		return
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
				update.callback_query.answer(strings.get("callback_simple", _lang))
		except:
			pass
		# Answer
		_button = InlineKeyboardButton(
			text=emoji.emojize(strings.get("button_help", _lang), use_aliases=True),
			callback_data="help"
		)
		_markup = InlineKeyboardMarkup(
			[[_button]]
		)
		bot.send_message(
			chat_id=update.effective_chat.id,
			text=strings.get("about", _lang),
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True,
			reply_markup=_markup
		)
	else:
		# Done: Button (2018-07-18)
		_button = InlineKeyboardButton(
			text=emoji.emojize(strings.get("button_about", _lang), use_aliases=True),
			url="https://telegram.me/%s?start=about" % bot.username
		)
		_markup = InlineKeyboardMarkup(
			[[_button]]
		)
		update.message.reply_text(
			"%s" % strings.get("about_public", _lang),
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True,
			reply_markup=_markup
		)
	return True


def cmd_help(bot, update):
	if not _spam_filter.verify(str(update.effective_user.id)):
		return
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
				update.callback_query.answer(strings.get("callback_simple", _lang))
		except:
			pass
		# Answer
		_button = InlineKeyboardButton(
			text=emoji.emojize(strings.get("button_help_advanced_caption", _lang), use_aliases=True),
			url=strings.get("button_help_advanced_url", _lang)
		)
		_markup = InlineKeyboardMarkup(
			[[_button]]
		)
		bot.send_message(
			chat_id=update.effective_chat.id,
			text=emoji.emojize(strings.get("help", _lang), use_aliases=True),
			parse_mode=ParseMode.MARKDOWN,
			reply_markup=_markup,
			disable_web_page_preview=True
		)
	else:
		# Done: Button (2018-07-18)
		_button = InlineKeyboardButton(
			text=emoji.emojize(strings.get("button_help", _lang), use_aliases=True),
			url="https://telegram.me/%s?start=help" % bot.username
		)
		_markup = InlineKeyboardMarkup(
			[[_button]]
		)
		update.message.reply_text(
			"%s" % strings.get("help_public", _lang),
			parse_mode=ParseMode.MARKDOWN,
			disable_web_page_preview=True,
			reply_markup=_markup
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
		if not _spam_filter.verify(str(update.effective_user.id)):
			return # ToDo: Return a message?
		if _paused:
			update.message.reply_text(text=emoji.emojize(strings.get("global_paused"), use_aliases=True), quote=True)
			return
		_username = update.effective_user.username
		if _username is None:
			_user_id = str(update.effective_user.id)
		else:
			_user_id = '@' + _username.lower()
		_address = None
		_rpc_call = __wallet_rpc.getaddressesbyaccount(_user_id)
		if not _rpc_call["success"]:
			print("Error during RPC call.")
			log("deposit", _user_id, "getaddressesbyaccount > Error during RPC call.")
		else:
			if _rpc_call["result"]["error"] is not None:
				print("Error: %s" % _rpc_call["result"]["error"])
				log("deposit", _user_id, "getaddressesbyaccount > Error: %s" % _rpc_call["result"]["error"])
			else:
				# Check if user already has an address. This will prevent creating another address if user has one
				_addresses = _rpc_call["result"]["result"]
				if len(_addresses) == 0:
					# Done: User has no address, request a new one (2018-07-16)
					_rpc_call = __wallet_rpc.getaccountaddress(_user_id)
					if not _rpc_call["success"]:
						print("Error during RPC call.")
						log("deposit", _user_id, "getaccountaddress > Error during RPC call.")
					else:
						if _rpc_call["result"]["error"] is not None:
							print("Error: %s" % _rpc_call["result"]["error"])
							log("deposit", _user_id, "getaccountaddress > Error: %s" % _rpc_call["result"]["error"])
						else:
							_address = _rpc_call["result"]["result"]
				else:
					_address = _addresses[0]
				# ToDo: Can it happen that a user gets more than juan address? Verify.
				if _address is not None:
					update.message.reply_text(
						text="%s `%s`" % (strings.get("user_address", _lang), _address),
						quote=True,
						parse_mode=ParseMode.MARKDOWN,
						disable_web_page_preview=True
					)


# Done: Give balance only if a private chat (2018-07-15)
# Done: Remove WorldCoinIndex (2018-07-15)
# ToDo: Add conversion
def balance(bot, update):
	if update.effective_chat is None:
		_chat_type = "private"
	elif update.effective_chat.type == "private":
		_chat_type = "private"
	else:
		_chat_type = "group"
	# Only show balance if it's a private conversation with the bot
	if _chat_type == "private":
		if not _spam_filter.verify(str(update.effective_user.id)):
			return # ToDo: Return a message?
		if _paused:
			update.message.reply_text(text=emoji.emojize(strings.get("global_paused"), use_aliases=True), quote=True)
			return
		# See issue #2 (https://github.com/DarthJahus/PandaTip-Telegram/issues/2)
		_username = update.effective_user.username
		if _username is None:
			_user_id = str(update.effective_user.id)
		else:
			_user_id = '@' + _username.lower()
		# get address of user
		_rpc_call = __wallet_rpc.getaddressesbyaccount(_user_id)
		if not _rpc_call["success"]:
			print("Error during RPC call: %s" % _rpc_call["message"])
			log("balance", _user_id, "(1) getaddressesbyaccount > Error during RPC call: %s" % _rpc_call["message"])
		elif _rpc_call["result"]["error"] is not None:
			print("Error: %s" % _rpc_call["result"]["error"])
			log("balance", _user_id, "(1) getaddressesbyaccount > Error: %s" % _rpc_call["result"]["error"])
		else:
			_addresses = _rpc_call["result"]["result"]
			if len(_addresses) == 0:
				# User has no address, ask him to create one
				update.message.reply_text(
					text=strings.get("user_no_address", _lang),
					quote=True
				)
			else:
				# ToDo: Handle the case when user has many addresses?
				# Maybe if something really weird happens and user ends up having more, we can calculate his balance.
				# This way, when asking for address (/deposit), we can return the first one.
				_address = _addresses[0]
				_rpc_call = __wallet_rpc.getbalance(_address)
				if not _rpc_call["success"]:
					print("Error during RPC call.")
					log("balance", _user_id, "(2) getbalance > Error during RPC call: %s" % _rpc_call["message"])
				elif _rpc_call["result"]["error"] is not None:
					print("Error: %s" % _rpc_call["result"]["error"])
					log("balance", _user_id, "(2) getbalance > Error: %s" % _rpc_call["result"]["error"])
				else:
					_balance = int(_rpc_call["result"]["result"])
					update.message.reply_text(
						text="%s\n`%i PND`" % (strings.get("user_balance", _lang), _balance),
						parse_mode=ParseMode.MARKDOWN,
						quote=True
					)


# Done: Rewrite the whole logic; use tags instead of parsing usernames (2018-07-15)
# Done: Allow private tipping if the user can be tagged (@username available) (Nothing to add for it to work.)
def tip(bot, update):
	"""
	/tip <user> <amount>
	/tip u1 u2 u3 ... v1 v2 v3 ...
	/tip u1 v1 u2 v2 u3 v3 ...
	"""
	if not _spam_filter.verify(str(update.effective_user.id)):
		return  # ToDo: Return a message?
	if _paused:
		update.message.reply_text(text=emoji.emojize(strings.get("global_paused"), use_aliases=True), quote=True)
		return
	# Get recipients and values
	_message = update.effective_message.text
	_modifier = 0
	_handled = {}
	_recipients = []
	for entity in update.effective_message.entities:
		if entity.type == "text_mention":
			# UserId is unique
			_username = entity.user.name
			if str(entity.user.id) not in _handled:
				_handled[str(entity.user.id)] = (_username, entity.offset, entity.length)
				_recipients.append(str(entity.user.id))
		elif entity.type == "mention":
			# _username starts with @
			# _username is unique
			_username = update.effective_message.text[entity.offset:(entity.offset+entity.length)].lower()
			if _username not in _handled:
				_handled[_username] = (_username, entity.offset, entity.length)
				_recipients.append(_username)
		_part = _message[:entity.offset-_modifier]
		_message = _message[:entity.offset-_modifier] + _message[entity.offset+entity.length-_modifier:]
		_modifier = entity.offset+entity.length-len(_part)
	print("_handled = %s" % _handled)
	print("_recipients = %s" % _recipients)
	_amounts = _message.split()
	# check if amounts are all convertible to float
	_amounts_float = []
	try:
		for _amount in _amounts:
			_amounts_float.append(convert_to_int(_amount))
	except:
		_amounts_float = []
	# Make sure number of recipients is the same as number of values
	# old: if len(_amounts_float) != len(_recipients) or len(_amounts_float) == 0 or len(_recipients) == 0:
	# new: ((len(_amounts_float) == len(_recipients)) or (len(_amounts_float) == 1)) and (len(_recipients) > 0),
	# use opposite
	if ((len(_amounts_float) != len(_recipients)) and (len(_amounts_float) != 1)) or (len(_recipients) == 0):
		update.message.reply_text(
			text=strings.get("tip_error_arguments", _lang),
			quote=True,
			parse_mode=ParseMode.MARKDOWN
		)
	else:
		#
		# Check if only 1 amount is given
		if len(_amounts_float) == 1 and len(_recipients) > 1:
			_amounts_float = _amounts_float * len(_recipients)
		# Check if user has enough balance
		_username = update.effective_user.username
		if _username is None:
			_user_id = str(update.effective_user.id)
		else:
			_user_id = '@' + _username.lower()
		# get address of user
		_rpc_call = __wallet_rpc.getaddressesbyaccount(_user_id)
		if not _rpc_call["success"]:
			print("Error during RPC call: %s" % _rpc_call["message"])
			log("tip", _user_id, "(1) getaddressesbyaccount > Error during RPC call: %s" % _rpc_call["message"])
		elif _rpc_call["result"]["error"] is not None:
			print("Error: %s" % _rpc_call["result"]["error"])
			log("tip", _user_id, "(1) getaddressesbyaccount > Error: %s" % _rpc_call["result"]["error"])
		else:
			_addresses = _rpc_call["result"]["result"]
			if len(_addresses) == 0:
				# User has no address, ask him to create one
				update.message.reply_text(
					text=strings.get("user_no_address", _lang),
					quote=True
				)
			else:
				_address = _addresses[0]
				# Get user's balance
				_rpc_call = __wallet_rpc.getbalance(_address)
				if not _rpc_call["success"]:
					print("Error during RPC call.")
					log("tip", _user_id, "(2) getbalance > Error during RPC call: %s" % _rpc_call["message"])
				elif _rpc_call["result"]["error"] is not None:
					print("Error: %s" % _rpc_call["result"]["error"])
					log("tip", _user_id, "(2) getbalance > Error: %s" % _rpc_call["result"]["error"])
				else:
					_balance = int(_rpc_call["result"]["result"])
					# Now, finally, check if user has enough funds (includes tx fee)
					if sum(_amounts_float) > _balance - max(1, int(len(_recipients)/3)):
						update.message.reply_text(
							text="%s `%i PND`" % (strings.get("tip_no_funds", _lang), sum(_amounts_float) + max(1, int(len(_recipients)/3))),
							quote=True,
							parse_mode=ParseMode.MARKDOWN
						)
					else:
						# Now create the {recipient_id: amount} dictionary
						i = 0
						_tip_dict = {}
						for _recipient in _recipients:
							# add "or _recipient == bot.id" to disallow tipping the tip bot
							if _recipient == _user_id:
								continue
							if _recipient[0] == '@':
								# ToDo: Get the id (actually not possible (Bot API 3.6, Feb. 2018)
								# See issue #2 (https://github.com/DarthJahus/PandaTip-Telegram/issues/2)
								# Using the @username
								# Done: When requesting a new address, if user has a @username, then use that username (2018-07-16)
								# Problem: If someone has no username, then later creates one, he loses access to his account
								# Done: Create a /scavenge command that allows people who had UserID to migrate to UserName (2018-07-16)
								_recipient_id = _recipient
							else:
								_recipient_id = _recipient
							# Check if recipient has an address (required for .sendmany()
							_rpc_call = __wallet_rpc.getaddressesbyaccount(_recipient_id)
							if not _rpc_call["success"]:
								print("Error during RPC call.")
								log("tip", _user_id,
									"(3) getaddressesbyaccount(%s) > Error during RPC call: %s" % (_recipient_id, _rpc_call["message"]))
							elif _rpc_call["result"]["error"] is not None:
								print("Error: %s" % _rpc_call["result"]["error"])
								log("tip", _user_id, "(3) getaddressesbyaccount(%s) > Error: %s" % (_recipient_id, _rpc_call["result"]["error"]))
							else:
								_address = None
								_addresses = _rpc_call["result"]["result"]
								if len(_addresses) == 0:
									# Recipient has no address, create one
									_rpc_call = __wallet_rpc.getaccountaddress(_recipient_id)
									if not _rpc_call["success"]:
										print("Error during RPC call.")
										log("tip", _user_id,
											"(4) getaccountaddress(%s) > Error during RPC call: %s" % (
											_recipient_id, _rpc_call["message"])
											)
									elif _rpc_call["result"]["error"] is not None:
										print("Error: %s" % _rpc_call["result"]["error"])
										log("tip", _user_id, "(4) getaccountaddress(%s) > Error: %s" % (
										_recipient_id, _rpc_call["result"]["error"]))
									else:
										_address = _rpc_call["result"]["result"]
								else:
									# Recipient has an address, we don't need to create one for him
									_address = _addresses[0]
							if _address is not None:
								# Because recipient has an address, we can add him to the dict
								_tip_dict[_recipient_id] = _amounts_float[i]
							i += 1
						#
						# Check if there are users left to tip
						if len(_tip_dict) == 0:
							return
						# Done: replace .move by .sendfrom or .sendmany (2018-07-16) 
						# sendfrom <from address or account> <receive address or account> <amount> [minconf=1] [comment] [comment-to]
						# and
						# sendmany <from address or account> {receive address or account:amount,...} [minconf=1] [comment]
						_rpc_call = __wallet_rpc.sendmany(_user_id, _tip_dict)
						if not _rpc_call["success"]:
							print("Error during RPC call.")
							log("tip", _user_id, "(4) sendmany > Error during RPC call: %s" % _rpc_call["message"])
						elif _rpc_call["result"]["error"] is not None:
							print("Error: %s" % _rpc_call["result"]["error"])
							log("tip", _user_id, "(4) sendmany > Error: %s" % _rpc_call["result"]["error"])
						else:
							_tx = _rpc_call["result"]["result"]
							_suppl = ""
							if len(_tip_dict) != len(_recipients):
								_suppl = "\n\n_%s_" % strings.get("tip_missing_recipient", _lang)
							update.message.reply_text(
								text = "*%s* %s\n%s\n\n[tx %s](%s)%s" % (
									update.effective_user.name,
									strings.get("tip_success", _lang),
									''.join((("\n- `%3.0f PND ` to *%s*" % (_tip_dict[_recipient_id], _handled[_recipient_id][0])) for _recipient_id in _tip_dict)),
									_tx[:4] + "..." + _tx[-4:],
									"https://chainz.cryptoid.info/pnd/tx.dws?" + _tx,
									_suppl
								),
								quote=True,
								parse_mode=ParseMode.MARKDOWN,
								disable_web_page_preview=True
							)


# Done: Revamp withdraw() function (2018-07-16)
def withdraw(bot, update, args):
	"""
	Withdraw to an address. Works only in private.
	"""
	if update.effective_chat is None:
		_chat_type = "private"
	elif update.effective_chat.type == "private":
		_chat_type = "private"
	else:
		_chat_type = "group"
	#
	if _chat_type == "private":
		if not _spam_filter.verify(str(update.effective_user.id)):
			return # ToDo: Return a message?
		if _paused:
			update.message.reply_text(text=emoji.emojize(strings.get("global_paused"), use_aliases=True), quote=True)
			return
		_amount = None
		_recipient = None
		if len(args) == 2:
			try:
				_amount = int(args[1])
				_recipient = args[0]
			except:
				try:
					_amount = int(args[0])
					_recipient = args[1]
				except:
					pass
		else:
			update.message.reply_text(
				text="Too few or too many arguments for this command.",
				quote=True
			)
		if _amount is not None and _recipient is not None:
			_username = update.effective_user.username
			if _username is None:
				_user_id = str(update.effective_user.id)
			else:
				_user_id = '@' + _username.lower()
			# get address of user
			_rpc_call = __wallet_rpc.getaddressesbyaccount(_user_id)
			if not _rpc_call["success"]:
				print("Error during RPC call: %s" % _rpc_call["message"])
				log("withdraw", _user_id, "(1) getaddressesbyaccount > Error during RPC call: %s" % _rpc_call["message"])
			elif _rpc_call["result"]["error"] is not None:
				print("Error: %s" % _rpc_call["result"]["error"])
				log("withdraw", _user_id, "(1) getaddressesbyaccount > Error: %s" % _rpc_call["result"]["error"])
			else:
				_addresses = _rpc_call["result"]["result"]
				if len(_addresses) == 0:
					# User has no address, ask him to create one
					update.message.reply_text(
						text=strings.get("user_no_address", _lang),
						quote=True
					)
				else:
					_address = _addresses[0]
					_rpc_call = __wallet_rpc.getbalance(_address)
					if not _rpc_call["success"]:
						print("Error during RPC call.")
						log("withdraw", _user_id, "(2) getbalance > Error during RPC call: %s" % _rpc_call["message"])
					elif _rpc_call["result"]["error"] is not None:
						print("Error: %s" % _rpc_call["result"]["error"])
						log("withdraw", _user_id, "(2) getbalance > Error: %s" % _rpc_call["result"]["error"])
					else:
						_balance = int(_rpc_call["result"]["result"])
						if _balance < _amount + 5:
							update.message.reply_text(
								text="%s `%i PND`" % (strings.get("withdraw_no_funds", _lang), _balance-5),
								quote=True,
								parse_mode=ParseMode.MARKDOWN
							)
						else:
							# Withdraw
							_rpc_call = __wallet_rpc.sendfrom(_user_id, _recipient, _amount)
							if not _rpc_call["success"]:
								print("Error during RPC call.")
								log("withdraw", _user_id, "(3) sendfrom > Error during RPC call: %s" % _rpc_call["message"])
							elif _rpc_call["result"]["error"] is not None:
								print("Error: %s" % _rpc_call["result"]["error"])
								log("withdraw", _user_id, "(3) sendfrom > Error: %s" % _rpc_call["result"]["error"])
							else:
								_tx = _rpc_call["result"]["result"]
								update.message.reply_text(
									text="%s\n[tx %s](%s)" % (
										strings.get("withdraw_success", _lang),
										_tx[:4]+"..."+_tx[-4:],
										"https://chainz.cryptoid.info/pnd/tx.dws?" + _tx
									),
									quote=True,
									parse_mode=ParseMode.MARKDOWN,
									disable_web_page_preview=True
								)


def scavenge(bot, update):
	if update.effective_chat is None:
		_chat_type = "private"
	elif update.effective_chat.type == "private":
		_chat_type = "private"
	else:
		_chat_type = "group"
	# Only if it's a private conversation with the bot
	if _chat_type == "private":
		if not _spam_filter.verify(str(update.effective_user.id)):
			return # ToDo: Return a message?
		if _paused:
			update.message.reply_text(text=emoji.emojize(strings.get("global_paused"), use_aliases=True), quote=True)
			return
		_username = update.effective_user.username
		if _username is None:
			update.message.reply_text(
				text="Sorry, this command is not for you.",
				quote=True
			)
		else:
			_username = '@' + _username.lower()
			_user_id = str(update.effective_user.id)
			# Done: Check balance of UserID (2018-07-16)
			# get address of user
			_rpc_call = __wallet_rpc.getaddressesbyaccount(_user_id)
			if not _rpc_call["success"]:
				print("Error during RPC call: %s" % _rpc_call["message"])
				log("scavenge", _user_id, "(1) getaddressesbyaccount > Error during RPC call: %s" % _rpc_call["message"])
			elif _rpc_call["result"]["error"] is not None:
				print("Error: %s" % _rpc_call["result"]["error"])
				log("scavenge", _user_id, "(1) getaddressesbyaccount > Error: %s" % _rpc_call["result"]["error"])
			else:
				_addresses = _rpc_call["result"]["result"]
				if len(_addresses) == 0:
					update.message.reply_text(
						text="%s (`%s`)" % (strings.get("scavenge_no_address", _lang), _user_id),
						quote=True,
					)
				else:
					_address = _addresses[0]
					_rpc_call = __wallet_rpc.getbalance(_address)
					if not _rpc_call["success"]:
						print("Error during RPC call.")
						log("scavenge", _user_id, "(2) getbalance > Error during RPC call: %s" % _rpc_call["message"])
					elif _rpc_call["result"]["error"] is not None:
						print("Error: %s" % _rpc_call["result"]["error"])
						log("scavenge", _user_id, "(2) getbalance > Error: %s" % _rpc_call["result"]["error"])
					else:
						_balance = int(_rpc_call["result"]["result"])
						# Done: Move balance from UserID to @username if balance > 5 (2018-07-16)
						if _balance <= 5:
							update.message.reply_text(
								text="%s (`ID %s`)." % (strings.get("scavenge_empty", _lang), _user_id),
								parse_mode=ParseMode.MARKDOWN,
								quote=True
							)
						else:
							# Need to make sure there is an account for _username
							_rpc_call = __wallet_rpc.getaddressesbyaccount(_username)
							if not _rpc_call["success"]:
								print("Error during RPC call: %s" % _rpc_call["message"])
								log("scavenge", _user_id, "(3) getaddressesbyaccount > Error during RPC call: %s" % _rpc_call["message"])
							elif _rpc_call["result"]["error"] is not None:
								print("Error: %s" % _rpc_call["result"]["error"])
								log("scavenge", _user_id, "(3) getaddressesbyaccount > Error: %s" % _rpc_call["result"]["error"])
							else:
								_address = None
								_addresses = _rpc_call["result"]["result"]
								if len(_addresses) == 0:
									# Create an address for user (_username)
									_rpc_call = __wallet_rpc.getaccountaddress(_username)
									if not _rpc_call["success"]:
										print("Error during RPC call.")
										log("scavenge", _user_id, "(4) getaccountaddress > Error during RPC call: %s" % _rpc_call["message"])
									elif _rpc_call["result"]["error"] is not None:
										print("Error: %s" % _rpc_call["result"]["error"])
										log("scavenge", _user_id, "(4) getaccountaddress > Error: %s" % _rpc_call["result"]["error"])
									else:
										_address = _rpc_call["result"]["result"]
								else:
									_address = _addresses[0]
								if _address is not None:
									# Move the funds from UserID to Username
									# ToDo: Make the fees consistent
									_rpc_call = __wallet_rpc.sendfrom(_user_id, _address, _balance-5)
									if not _rpc_call["success"]:
										print("Error during RPC call.")
										log("scavenge", _user_id, "(5) sendfrom > Error during RPC call: %s" % _rpc_call["message"])
									elif _rpc_call["result"]["error"] is not None:
										print("Error: %s" % _rpc_call["result"]["error"])
										log("scavenge", _user_id, "(5) sendfrom > Error: %s" % _rpc_call["result"]["error"])
									else:
										_tx = _rpc_call["result"]["result"]
										update.message.reply_text(
											text="%s (`%s`).\n%s `%i PND`\n[tx %s](%s)" % (
												strings.get("scavenge_success_1", _lang),
												_user_id,
												strings.get("scavenge_success_2", _lang),
												_balance-5,
												_tx[:4]+"..."+_tx[-4:],
												"https://chainz.cryptoid.info/pnd/tx.dws?" + _tx,
											),
											quote=True,
											parse_mode=ParseMode.MARKDOWN,
											disable_web_page_preview=True
										)


def convert_to_int(text):
	# with panda feature :D (2018-07-18)
	try:
		# try convert to float
		return int(text)
	except:
		# Check if the text is made of pandas
		if len(text)/2 > 3 or len(text) == 0 or len(text) % 2 != 0:
			raise ValueError("Can't convert %s to int." % text)
		else:
			_panda = emoji.emojize(":panda_face:", use_aliases=True)
			print(len(text))
			for i in range(len(text)):
				if text[i] != _panda[i%2]:
					raise ValueError("Can't convert %s to int." % text)
			else:
				return 10**(int(len(text)/2))


def cmd_send_log(bot, update):
	"""
	Send logs to (admin) user
	"""
	# Note: Don't use emoji in caption
	# Check if admin
	if update.effective_chat.id in config["admins"]:
		with open("log.csv", "rb") as _file:
			_file_name = "%s-log-%s.csv" % (bot.username, datetime.fromtimestamp(time.time()).strftime("%Y-%m-%dT%H-%M-%S"))
			bot.sendDocument(
				chat_id=update.effective_user.id,
				document=_file,
				reply_to_message_id=update.message.message_id,
				caption="Here you are!",
				filename=_file_name
			)
		log(fun="cmd_send_log", user=str(update.effective_user.id), message="Log sent to admin '%s'." % update.effective_user.name)


def cmd_clear_log(bot, update):
	if update.effective_chat in config["admins"]:
		clear_log()
		update.message.reply_text(text=emoji.emojize(strings.get("clear_log_done"), use_aliases=True))


def cmd_pause(bot, update):
	# Admins only
	if update.effective_chat.id in config["admins"]:
		global _paused
		_paused = not _paused
		_answer = ""
		if _paused:
			_answer = strings.get("pause_answer_paused")
		else:
			_answer = strings.get("pause_answer_resumed")
		update.message.reply_text(emoji.emojize(_answer, use_aliases=True), quote=True)


# ToDo: Revamp functions bellow


def price(bot, update):
	pass


def marketcap(bot, update):
	pass


def hi(bot, update):
	if not _spam_filter.verify(str(update.effective_user.id)):
		return  # ToDo: Return a message?
	user = update.message.from_user.username
	bot.send_message(chat_id=update.message.chat_id, text="Hello @{0}, how are you doing today?".format(user))


def moon(bot, update):
	update.message.reply_text(text="Moon mission inbound!")


def market_cap(bot, update):
	pass


if __name__ == "__main__":
	updater = Updater(token=config["telegram-token"])
	dispatcher = updater.dispatcher
	# TGBot commands
	dispatcher.add_handler(CommandHandler('start', cmd_start, pass_args=True))
	dispatcher.add_handler(CommandHandler('help', cmd_help))
	dispatcher.add_handler(CallbackQueryHandler(callback=cmd_help, pattern=r'^help$'))
	dispatcher.add_handler(CommandHandler('about', cmd_about))
	dispatcher.add_handler(CallbackQueryHandler(callback=cmd_about, pattern=r'^about$'))
	# Funny commands
	dispatcher.add_handler(CommandHandler('moon', moon))
	dispatcher.add_handler(CommandHandler('hi', hi))
	# Tipbot commands
	dispatcher.add_handler(CommandHandler('tip', tip))
	dispatcher.add_handler(CommandHandler('withdraw', withdraw, pass_args=True))
	dispatcher.add_handler(CommandHandler('deposit', deposit))
	dispatcher.add_handler(CommandHandler('address', deposit)) # alias for /deposit
	dispatcher.add_handler(CommandHandler('balance', balance))
	dispatcher.add_handler(CommandHandler("scavenge", scavenge))
	# Conversion commands
	dispatcher.add_handler(CommandHandler('marketcap', marketcap))
	dispatcher.add_handler(CommandHandler('price', price))
	# Admin commands
	dispatcher.add_handler(CommandHandler("send_log", cmd_send_log))
	dispatcher.add_handler(CommandHandler("get_log", cmd_send_log))
	dispatcher.add_handler(CommandHandler("clear_log", cmd_clear_log))
	dispatcher.add_handler(CommandHandler("pause", cmd_pause)) # pause / unpause
	updater.start_polling()
	log("__main__", "__system__", "Started service!")
