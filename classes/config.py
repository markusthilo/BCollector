#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from configparser import ConfigParser

class Config:
	'''Configuration file'''

	def __init__(self, path):
		'''Get configuration from file'''
		config = ConfigParser()
		config.read(path)
		self.source_url = config['SOURCE']['url']
		self.source_xpath = config['SOURCE']['xpath']
		self.pgp_cmd = Path(config['PGP']['command'])
		self.pgp_passphrase = config['PGP']['passphrase']
		self.dst_dir_path = Path(config['Directories']['destination'])
		self.log_dir_path = Path(config['Directories']['logging'])
		self.backup_dir_path = Path(config['Directories']['backup'])
		self.minutes = [int(minute.strip(' ')) for minute in config['GENERAL']['minutes'].split(',')]
		self.retries = int(config['GENERAL']['retries'])
		self.delay = int(config['GENERAL']['delay'])
		self.sleep = int(config['GENERAL']['sleep'])
		self.keep = int(config['GENERAL']['keep']) * 2629746	# time delta in seconds to keep files