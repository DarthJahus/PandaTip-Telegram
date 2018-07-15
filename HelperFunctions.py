import json


def load_file_json(file_name):
	with open(file_name, 'r') as _file:
		content = _file.read()
		content_dict = json.loads(content)
		_file.close()
		return content_dict


class Strings:
	def __init__(self, file):
		self.dict = load_file_json(file)

	def get(self, item, lang):
		return '\n'.join(self.dict[item][lang])


if __name__ == "__main__":
	str = Strings("strings.json")
	print(str.get("help", "en"))
