#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from configparser import ConfigParser
from pathlib import Path

class Config(ConfigParser):
	'''Configuration from file'''

	def __init__(self, path):
		'''Read configuration from file'''
		super().__init__()
		self.read(path)

	def getpath(self, key):
		'''Get pathlib.Path object'''
		string = self['LOCAL'].get(key)
		if string:
			return Path(string)

	def getloop(self, key):
		'''Get loop configuration for given key'''
		string = self.get('LOOP', key)
		if not string.lower() in ('', 'all', 'every', 'each', '*', '.'):
			return tuple(int(i.strip()) for i in string.split(','))
