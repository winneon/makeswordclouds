import json
import re

from os import path

class Config:
	def __init__(self, name, template):
		self.config_path = path.dirname(path.dirname(__file__)) + name

		if not path.isfile(self.config_path):
			self._write(self.config_path, template)

		self.config = json.loads(open(self.config_path).read())

	def _write(self, filepath, template):
		with open(filepath, "w") as w:
			w.write(json.dumps(template, indent=4, sort_keys=True))

	def get(self):
		return self.config

	def save(self):
		self._write(self.config_path, self.config)