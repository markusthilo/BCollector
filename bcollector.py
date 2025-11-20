#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.3.0_2025-11-20'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Fetch gpg encrypted files, save them on backup and export decrypted to target'

import logging
from pathlib import Path
from sys import exit as sysexit
from time import sleep as t_sleep
from datetime import datetime
from argparse import ArgumentParser
from classes.config import Config
from classes.logger import Logger
from classes.httpdownloader import HttpDownloader
from classes.pgpdecoder import PgpDecoder
from classes.backup import Backup

class Worker:
	'''Do the work'''

	def __init__(self, config):
		'''Definitions'''
		self._downloader = HttpDownloader(url, xpath, config._backup_dir_path,
			retries = config.retries,
			delay = config.delay
		)
		self._dst_dir_path = config.dst_dir_path
		self._backup = Backup(config.backup_dir_path, config.keep)
		self._decoder = PgpDecoder(config.pgp_cmd, config.pgp_passphrase)

	def download(self):
		'''Download files'''
		local_filenames = [path.name for path in self._backup.ls()]
		remote_filenames = downloader.ls()
		if not remote_filenames:
			continue
		for filename in remote_filenames:
			if filename in local_filenames:
				continue
			pts = filename.split('_')
			try:
				dir_path = self.target_dir_path / f'{pts[0]}_{pts[1]}_{pts[2]}/{pts[0]}{pts[2][2:].replace("-", "")}'
				file_path = dir_path / filename[:-4]
				dir_path.mkdir(parents=True, exist_ok=True)
				encrypted_path = downloader.download(filename)
				if not encrypted_path:
					raise TimeoutError(f'Unable to download {filename}')
				if file_path.exists():
					raise FileExistsError(f'{file_path} is already present')
				decrypted_path = self._decoder.decode(encrypted_path, file_path)
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

	def loop(self, minutes, sleep, logger):
		'''Endless loop for daemon mode'''
		month = datetime.today().month
		while True:
			self._backup.purge()
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
