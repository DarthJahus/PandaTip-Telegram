# Jahus, 2018-01-28

import requests
import json
from functools import partial
from HelperFunctions import load_file_json
import sys, traceback
import urllib3; urllib3.disable_warnings()


class MethodMissing:
	def method_missing(self, name, *args, **kwargs):
		print("Command %s with args %s and additional args %s" % (name, args, kwargs))

	def __getattr__(self, name):
		return partial(self.method_missing, name)


class Wrapper(object, MethodMissing):
	def __init__(self, item):
		self.item = item

	def method_missing(self, name, *args, **kwargs):
		if name in dir(self.item):
			method = getattr(self.item, name)
			if callable(method):
				return method(*args, **kwargs)
			else:
				raise AttributeError('Method "%s" is not callable in %s' % (name, self.item))
		else:
			# raise AttributeError(" %s called with args %s and %s " % (name, args, kwargs))
			return self.http_post_request(name, args)


class PandaRPC(object):
	def __init__(self, uri, auth):
		self.uri = uri
		self.auth = auth

	def http_post_request(self, name, args):
		data = {"jsonrpc": "1.0", "id": "pandatip", "method": name, "params": args}
		try:
			req = requests.post(
				url=self.uri,
				auth=self.auth,
				data=json.dumps(data),
				headers={"content-type": "text/plain", "connection": "close"}
			)
			if req.status_code != 200:
				return {"success": False, "message": req.status_code}
			else:
				return {"success": True, "result": req.json()}
		except requests.exceptions.ConnectionError:
			return {"success": False, "message": "ConnectionError exception."}
		except:
			_message = "Unexpected error occurred. No traceback available."
			try:
				exc_info = sys.exc_info()
			finally:
				_traceback = traceback.format_exception(*exc_info)
				del exc_info
				_message = "Unexpected error occurred. | Name: %s | Args: %s | Traceback:\n%s\n" % (
					name,
					args,
					''.join(_traceback)
				)
			return {"success": False, "message": _message}


def main():
	_config = load_file_json("config.json") 
	myPanda = Wrapper(PandaRPC(_config["rpc-uri"], (_config["rpc-user"], _config["rpc-psw"])))
	# getaccountaddress creates an address if account doesn't exist
	res = myPanda.getaddressesbyaccount("tmp")
	if not res["success"]:
		print("Error: %s" % res["message"])
	else:
		if res["result"]["error"] is not None:
			print("Error: %s" % res["result"]["error"])
		else:
			print(json.dumps(res["result"]["result"]))
	return
	res = myPanda.sendmany("PandaTip", {"@jahus": 5, "1234": 6})
	if not res["success"]:
		print("Error: %s" % res["message"])
	else:
		if res["result"]["error"] is not None:
			print("Error: %s" % res["result"]["error"])
		else:
			print(json.dumps(res["result"]["result"]))


if __name__ == "__main__":
	main()
