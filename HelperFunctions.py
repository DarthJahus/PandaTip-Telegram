import json
import time
from datetime import datetime
import codecs


def load_file_json(file_name):
	with open(file_name, 'r') as _file:
		content = _file.read()
		content_dict = json.loads(content)
		_file.close()
		return content_dict


class Strings:
	def __init__(self, file):
		self.dict = load_file_json(file)

	def get(self, item, lang="en"):
		_lang_fail_over = "en"
		if lang not in self.dict[item]:
			return '\n'.join(self.dict[item][_lang_fail_over])
		else:
			return '\n'.join(self.dict[item][lang])


def log(fun, user, message, debug=True):
	# type: (str, str, str, bool) -> None
	"""
	Log in a CSV file
	Header is:
	"time", "command", "user_id", "message"
	Time is in local-time
	:rtype: None
	"""
	_log = (
		datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S") + ',' +
		','.join([fun, user, "\"" + message.replace('\"', '\'').replace('\n', '|') + "\""]) + "\n"
	)
	with codecs.open("log.csv", 'a', "utf-8") as _file:
		_file.write(_log)
		if debug: print("*log = " + _log)


def clear_log(debug=False):
	codecs.open("log.csv", 'w', "utf-8").close()
	if debug: print(">>> CLEARED LOG")


class AntiSpamFilter:

	def __init__(self, max_events, time_span):
		self.db = {}
		self.max_events = max_events
		self.time_span = time_span

	def verify(self, entity, add=True):
		if entity.lower() not in self.db:
			self.db[entity.lower()] = {
				"count": int(add),
				"start_time": time.time()
			}
			return True
		else:
			self.db[entity.lower()]["count"] += int(add)
			_count = self.db[entity.lower()]["count"]
			_start_time = self.db[entity.lower()]["start_time"]
			if _count > self.max_events:
				if (time.time() - _start_time) <= self.time_span:
					return False
				else:
					self.db[entity.lower()]["count"] = 0
					self.db[entity.lower()]["start_time"] = time.time()
					return True
			else:
				return True


if __name__ == "__main__":
	str = Strings("strings.json")
	print(str.get("help", "en"))
