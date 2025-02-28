#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.2.0_2025-02-26'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Fetch gpg encrypted files, save them on backup and export decrypted to target'

import logging
from pathlib import Path
from sys import exit as sysexit
from time import sleep as t_sleep
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
		self.sources = [
			(config[section]['url'], config[section]['xpath'])
			for section in config.sections() if section.startswith('SOURCE')
		]
		self.pgp_cmd = Path(config['PGP']['command'])
		self.pgp_passphrase = config['PGP']['passphrase']
		self.target_dir_path = Path(config['TARGET']['dir'])
		self.log_dir_path = Path(config['LOG']['dir'])
		self.tmp_dir_path = Path(config['TMP']['dir'])
		self.minutes = [int(minute.strip(' ')) for minute in config['GENERAL']['minutes'].split(',')]
		self.retries = int(config['GENERAL']['retries'])
		self.delay = int(config['GENERAL']['delay'])
		self.sleep = int(config['GENERAL']['sleep'])
		self.keep = int(config['GENERAL']['keep']) * 2629746	# time delta in seconds to keep files

class TempDir:
	'''Handle the backup'''

	def __init__(self, path, keep):
		'''Create object for the backup directory'''
		self.path = path
		self.keep = keep

	def ls(self):
		'''List files in backup directory'''
		return (path for path in self.path.glob('*.zip.pgp'))

	def get_expired(self):
		'''Get the files that were created before given time delta'''
		oldest = datetime.timestamp(datetime.now()) - self.keep
		return (path for path in self.ls() if path.stat().st_mtime < oldest)

	def purge(self):
		'''Delete all files in backup directory that are expired'''
		for path in self.get_expired():
			try:
				path.unlink()
			except Exception as e:
				msg = f'Unable to remove expired file {path}:\n{e}'
				logging.error(msg)
				msg = f'ERROR: {msg}'
			else:
				msg = f'Removed expired file {path}'
				logging.info(msg)
				msg = f'INFO: {msg}'
			if logging.root.level == logging.DEBUG:
				print(msg)

class Collector:
	'''Functionality to process the whole file transfer'''

	def __init__(self, config):
		'''Definitions'''
		self.downloaders = [HttpDownloader(url, xpath, config.tmp_dir_path, retries=config.retries, delay=config.delay)
			for url, xpath in config.sources
		]
		self.target_dir_path = config.target_dir_path
		self.tmp_dir = TempDir(config.tmp_dir_path, config.keep)
		self.decoder = PgpDecoder(config.pgp_cmd, config.pgp_passphrase)

	def download(self):
		'''Download files'''
		tmp_filenames = [path.name for path in self.tmp_dir.ls()]
		for downloader in self.downloaders:
			srv_filenames = downloader.ls()
			if not srv_filenames:
				continue
			for filename in srv_filenames:
				if filename in tmp_filenames:
					continue
				pts = filename.split('_')
				try:
					dir_path = self.target_dir_path / f'{pts[0]}_{pts[1]}_{pts[2]}/{pts[0]}{pts[2][2:].replace("-", "")}'
					file_path = dir_path / filename[:-4]
					if file_path.exists():
						raise FileExistsError(f'{file_path} is already present')
					dir_path.mkdir(parents=True, exist_ok=True)
					encrypted_path = downloader.download(filename)
					if not encrypted_path:
						raise TimeoutError(f'Unable to download {filename}')
					decrypted_path = self.decoder.decode(encrypted_path, file_path)
					if not decrypted_path:
						raise RuntimeError(f'Unable to decode {encrypted_path}')
				except Exception as e:
					msg = f'Did not retrieve {filename}:\n{e}'
					logging.warning(msg)
					msg = f'WARNING: {msg}'
				else:
					msg = f'Download process generated {decrypted_path} and {encrypted_path}'
					logging.info(msg)
					msg = f'INFO: {msg}'
				if logging.root.level == logging.DEBUG:
					print(msg)
		msg = 'Check or download has finished'
		logging.info(msg)
		if logging.root.level == logging.DEBUG:
			print(f'INFO: {msg}')

class Worker(Collector):
	'''Do the work'''

	def loop(self, minutes, sleep, logger):
		'''Endless loop for daemon mode'''
		month = datetime.today().month
		while True:
			self.tmp_dir.purge()
			this_minute = int(datetime.now().strftime('%M'))
			if this_minute in minutes:
				self.download()
			this_month = datetime.today().month
			if this_month != month:
				logger.rotate()
				month = this_month
			t_sleep(sleep)

if __name__ == '__main__':	# start here if called as application
	this_script_path = Path(__file__)
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-c', '--config',
		type = Path,
		help = 'Set path to config file',
		metavar = 'FILE',
		default = this_script_path.with_suffix('.conf')
	)
	argparser.add_argument('-l', '--loglevel',
		type = str,
		help = 'Log level: debug, info (default), warning, error or critical',
		metavar = 'STRING',
		choices= ['debug', 'info', 'warning', 'error', 'critical'],
		default = 'info'
	)
	args = argparser.parse_args()
	config = Config(args.config)
	logger = Logger(level=args.loglevel, dir=config.log_dir_path)
	worker = Worker(config)
	if logging.root.level == logging.DEBUG:
		logging.debug('Starting download on debug level now and for once')
		worker.download()
		sysexit(0)
	else:
		logging.info('Starting main loop')
		try:
			worker.loop(config.minutes, config.sleep, logger)
		except KeyboardInterrupt:
			logging.info('Main loop terminated by Ctrl-C')
			sysexit(0)
