#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.1_2024-11-30'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Fetch gpg encrypted files, save them on backup and export to target'

import logging
from pathlib import Path
from sys import exit as sysexit
from time import sleep
from datetime import datetime
from configparser import ConfigParser
from argparse import ArgumentParser, FileType
### Custom Libraries ###
from lib.logger import Logger
from lib.httpdownloader import HttpDownloader
from lib.pgpdecoder import PgpDecoder

class Config:
	'''Configuration file'''

	def __init__(self, path):
		'''Get configuration from file'''
		self.path = path
		config = ConfigParser()
		config.read(self.path)
		self.sources = {
			section: {
				'url':		config[section]['url'],
				'xpath':	config[section]['xpath'],
				'minutes':	[int(minute.strip(' ')) for minute in config[section]['minutes'].split(',')],
				'target':	Path(config[section]['target']),
				'backup':	Path(config[section]['backup']),
			} for section in config.sections() if section.startswith('SOURCE')
		}
		self.retries = int(config['GENERAL']['retries'])
		self.retrydelay = int(config['GENERAL']['delay'])
		self.sleep = int(config['GENERAL']['sleep'])
		self.keep = int(config['GENERAL']['keep']) * 2629746	# time delta in seconds to keep files
		self.pgp_cmd = Path(config['PGP']['command'])
		self.pgp_passphrase = config['PGP']['passphrase']
		self.logdir = Path(config['LOG']['dir'])

class Backup:
	'''Handle the backup'''

	def __init__(self, config):
		'''Create object for the backup directory'''
		self.config = config

	def ls(self, source):
		'''List files in backup directory'''
		return (path for path in self.config.sources[source]['backup'].glob('*') if path.is_file())

	def get_expired(self, source):
		'''Get the files that were created before given time delta'''
		oldest = datetime.timestamp(datetime.now()) - self.config.keep
		return (path for path in self.ls(source) if path.stat().st_mtime < oldest)

	def purge(self):
		'''Delete all files in backup directory that are expired'''
		for source in self.config.sources:
			for path in self.get_expired(source):
				try:
					path.unlink()
				except Exception as e:
					logging.error(f'Unable to remove expired file {path}:\n{e}')
				else:
					logging.info(f'Removed expired file {path}')

class Collector:
	'''Functionality to process the whole file transfer'''

	def __init__(self, config):
		'File transfer'
		self.config = config
		self.backup = Backup(self.config)
		self.decoder = PgpDecoder(self.config.pgp_cmd, self.config.pgp_passphrase)

	def run(self, source):
		'''Run one collection'''
		downloader = HttpDownloader(
			self.config.sources[source]['url'],
			self.config.sources[source]['xpath']
		)
		for filename in set(downloader.ls()) - {path.name for path in self.backup.ls(source)}:
			backup_path = downloader.download(filename, config.sources[source]['backup'])
			if backup_path:
				decrypted_path = self.decoder.decode(encrypted_path, dir_path)
				if decrypted_path:
					logging.info(f'Download process generated {decrypted_path} and {backup_path}')

	def run_all(self):
		'''Run collection from every server'''
		for source in self.config.sources:
			self.run(source)

class Worker(Collector):
	'''Do the work'''

	def loop(self):
		'''Endless loop for doemon mode'''
		while True:
			self.backup.purge()
			this_minute = int(datetime.now().strftime('%M'))
			for source in self.config.sources:
				if this_minute in self.config.sources[source]['minutes']:
					try:
						self.collector.run(source)
					except Exception as e:
						logging.error(f'Something went wrong in mail loop while checking {source}:\n{e}')
			sleep(self.config.sleep)

if __name__ == '__main__':	# start here if called as application
	this_script_path = Path(__file__)
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-c', '--config',
		type = Path,
		help = 'Config file',
		metavar = 'FILE',
		default = this_script_path.with_suffix('.conf')
	)
	argparser.add_argument('-l', '--loglevel',
		type = str,
		help = 'Log level',
		metavar = 'STRING',
		choices= ['debug', 'info', 'warning', 'error', 'critical'],
		default = 'info'
	)
	args = argparser.parse_args()
	config = Config(args.config)
	Logger(level=args.loglevel, dir=config.logdir)
	worker = Worker(config)
	if logging.root.level == logging.DEBUG:
		logging.debug('Starting download on debug level now and for once')
		worker.run_all()
		print(config.path.read_text(encoding='utf-8'))
		sysexit(0)
	else:
		logging.info('Starting main loop')
		worker.loop()
