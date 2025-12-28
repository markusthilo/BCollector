#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.4.2_2025-12-28'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Sync remote and local files. HTTP(S) and SFTP are possible protocols. Forward to final destination, decryptPGP/GPG encrypted files.'

from datetime import datetime
from time import sleep
from argparse import ArgumentParser
from pathlib import Path
from configparser import ConfigParser
from sys import exit
from classes.config import Config
from classes.localdirs import LocalDirs
from classes.filedb import FileDB
from classes.httpdownloader import HTTPDownloader
from classes.sftpdownloader import SFTPDownloader
from classes.pgpdecryptor import PGPDecryptor
from classes.logger import Logger as Log

class BCollector:
	'''Sync loacl with remote'''

	def __init__(self, url, download_path, destination_path, db_path,
		password = None,
		timeout = None,
		retries = None,
		delay = None,
		decryptor = None,
		wait = False,
		trigger = None,
		keep = 0
	):
		'''Definitions'''
		self._url = f'{url.rstrip("/")}/'
		self._local = LocalDirs(download_path, destination_path, decryptor=decryptor, trigger=trigger)
		self._db = FileDB(db_path)
		protocol = self._url.split(':', 1)[0].lower()
		if protocol == 'http':
			self._downloader = HTTPDownloader(url, retries=retries, delay=delay)
		elif protocol == 'sftp':
			self._downloader = SFTPDownloader(url, password, timeout=timeout, retries=retries, delay=delay)
		else:
			raise ValueError(f'Unknown protocol {protocol}')
		self._wait = wait
		self._trigger = bool(trigger)
		self._keep = keep * 60	# from minutes to seconds
		self._new_file_paths = list()

	def find(self, name=None):
		'''List remote files'''
		self._downloader.open_connection()
		for path in self._downloader.find(name=name):
			yield path, self._url + f'{path}'.replace('\\', '/')
		self._downloader.close_connection()

	def download(self, name=None):
		'''Download files'''
		self._downloader.open_connection()
		for relative_path in set(self._downloader.find(name=name)) - set(self._db.get_all()):
			if self._local.mk_download_dir(relative_path):
				download_file_path = self._downloader.download(relative_path, self._local.download_path)
				if download_file_path:
					self._db.add_download(relative_path)
					Log.info(f'Downloaded {download_file_path}')
		self._downloader.close_connection()

	def forward(self):
		'''Forward downloaded files to final destination'''
		if self._wait and self._local.destination_path.exists():
			Log.debug(f'Destination directory {self._local.destination_path} exists')
			return 0
		forwarded = 0
		for relative_path in self._db.get_not_forwarded():
			if destination_file_path := self._local.forward(relative_path):
				self._db.mark_forward(relative_path)
				forwarded += 1
				if not self._keep:
					self._db.delete(relative_path)
				Log.info(f'Created {destination_file_path}')
			else:
				Log.error(f'Unable to forward {relative_path}')
		if self._trigger and forwarded:
			self._local.write_trigger()
		return forwarded

	def loop(self, log=None, hours=None, minutes=None, clean=None):
		'''Endless loop for daemon mode'''
		Log.info(f'Starting main loop: hours = {hours}, minutes = {minutes}, clean = {clean}h, keep = {self._keep} minute(s)')
		clean_ts = check_ts = 0
		while True:
			now = datetime.now()
			now_ts = int(now.timestamp())
			if self._keep and clean and clean == now.hour and now_ts - clean_ts >= 3600:
				Log.info(f'Looking for expired downloaded files')
				expired = tuple(relative_path in self._db.get_older_than(now_ts - self._keep))
				if expired:
					Log.info(f'Found {len(expired)} expired files')
					for relative_path in self._local.clean_download(expired):
						self._db.delete(relative_path)
				clean_ts = now_ts
			if (not hours or now.hour in hours) and (not minutes or now.minute in minutes) and now_ts - check_ts >= 60:
				Log.info('Checking')
				Log.debug('Checking remote location')
				try:
					self.download()
				except:
					Log.error('A problem occured while checking for new remote files')
				else:
					Log.debug('Finished checking remote location')
				Log.debug('Checking local downloads')
				try:
					self.forward()
				except:
					Log.error('A problem occured while checking for files to forward')
				else:
					Log.debug('Finished checking local downloads')
				if log:
					Log.debug('Checking log file size')
					try:
						log.check_size()
					except:
						Log.error('Unable to check log file size')
					else:
						Log.debug('Finished checking log file size')
				check_ts = now_ts
			delta = now_ts - check_ts
			if delta < 60:
				sleep(60 - delta)

if __name__ == '__main__':	# start here if called as application
	default_config_path = Path(__file__).with_suffix('.conf')
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-c', '--config',
		type = Path,
		help = f'Set path to config file (default: {default_config_path})',
		metavar = 'FILE',
		default = default_config_path
	)
	argparser.add_argument('-d', '--debug',
		action = 'store_true',
		help = 'Set log level to debug (overwrites -l/--loglevel)',
	)
	argparser.add_argument('-l', '--loglevel',
		type = str,
		help = 'Log level: debug, info (default), warning, error or critical',
		metavar = 'STRING',
		choices= ['debug', 'info', 'warning', 'error', 'critical'],
		default = 'info'
	)
	argparser.add_argument('-s', '--simulate',
		action = 'store_true',
		help = 'Simulate: connect to server and list file, do not download any data',
	)
	args = argparser.parse_args()
	logger = Log('debug') if args.simulate or args.debug else Log(args.loglevel)
	config_none = ('', 'none', 'no', 'false', '0')
	try:
		config = Config(args.config)
	except:
		Log.critical(f'Unable to read config file {args.config}')
	log = config['LOCAL'].get('logfile', '')
	if not log.lower() in config_none:
		try:
			logger.add_file(Path(log), max_size=config['LOCAL'].getint('logsize', 0)*1048576)
		except:
			Log.critical(f'Unable to create log file')
		Log.debug(f'Logging to {log}')
	name = config['REMOTE'].get('name', '')
	name = name if not name in ('', '.', '*', '.*') else None
	encryption = config['REMOTE'].get('encryption')
	if encryption:
		encryption = encryption.lower()
		if encryption in config_none:
			decryptor = None
		elif encryption in ('pgp', 'gpg'):
			try:
				decryptor = PGPDecryptor(passphrase = config['REMOTE'].get('passphrase', ''))
			except:
				Log.critical(f'Unable to setup decryptor for {encryption}')
		else:
			Log.critical(f'Unknown encryption: {encryption}')
	else:
		decryptor = None
	collector = BCollector(
		config['REMOTE'].get('url'),
		config.getpath('download'),
		config.getpath('destination'),
		config.getpath('db'),
		password = config['REMOTE'].get('password'),
		timeout = config['REMOTE'].getint('timeout'),
		retries = config['REMOTE'].getint('retries'),
		delay = config['REMOTE'].getint('delay'),
		decryptor = decryptor,
		wait = config['LOCAL'].getboolean('wait'),
		trigger = config.getpath('trigger'),
		keep = config['LOCAL'].getint('keep', 0)
	)
	if args.simulate:
		Log.info('Reading remote structure')
		for path, url in collector.find(name=name):
			Log.info(f'Seeing file: {path} / URL: {url}')
	elif config['LOOP'].getboolean('enable'):
		Log.info('Starting main loop')
		try:
			collector.loop(logger,
				hours = config.getloop('hours'),
				minutes = config.getloop('minutes'),
				clean = config['LOOP'].get('clean')
			)
		except KeyboardInterrupt:
			print()
			Log.info('Main loop terminated by Ctrl-C')
			exit(0)
	else:
		Log.info('Starting download')
		collector.download(name=name)
		collector.forward()
	Log.info('Done')
	exit(0)
