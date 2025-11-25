#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.4.0_2025-11-26'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Sync remote and local files. HTTP and SFTP are possible protocols. Forward to final destination, decrypt gpg encrypted files.'

from datetime import datetime
from time import sleep
from argparse import ArgumentParser
from pathlib import Path
from configparser import ConfigParser
from sys import exit
from classes.localdirs import LocalDirs
from classes.httpdownloader import HTTPDownloader
from classes.sftpdownloader import SFTPDownloader
from classes.pgpdecryptor import PGPDecryptor
from classes.logger import Logger as Log

class BCollector:
	'''Sync loacl with remote'''

	def __init__(self, url, download_path, destination_path,
		password = None,
		timeout = None,
		retries = None,
		delay = None,
		decryptor = None
	):
		'''Definitions'''
		self._url = url.rstrip('/')
		self._local = LocalDirs(download_path, destination_path, decryptor=decryptor)
		protocol = self._url.split(':', 1)[0].lower()
		if protocol == 'http':
			self._downloader = HTTPDownloader(url, retries=retries, delay=delay)
		elif protocol == 'sftp':
			self._downloader = SFTPDownloader(url, password, timeout=timeout, retries=retries, delay=delay)
		else:
			raise ValueError(f'Unknown protocol {protocol}')

	def find(self, name=None):
		'''List remote files, regex filter filename'''
		for path in self._downloader.find(name):
			yield path

	def download(self, name=None):
		'''Download files'''
		for relative_path in set(self._downloader.find(name=name)) - set(self._local.rglob_download()):
			if not self._local.mk_download_dir(relative_path):
				continue
			download_file_path = self._downloader.download(relative_path, self._local._download_path)
			if download_file_path:
				Log.info(f'Downloaded {download_file_path}')
				if destination_file_path := self._local.forward(download_file_path):
					Log.info(f'Created {destination_file_path}')

	def loop(self, logger, delay=None, hours=None, minutes=None, clean=None, keep=0):
		'''Endless loop for daemon mode'''
		delay = delay if delay else 10
		keep_sec = keep * 2629746	# adjust time delta from months to seconds
		Log.info(f'Starting main loop: delay = {delay}s, hours = {hours}, minutes = {minutes}, clean = {clean}h, keep = {keep} month(s)')
		while True:
			now = datetime.now()
			if clean and keep and clean == now.hour:
				Log.info(f'Cleaning up download directory')
				self._local.clean_download(keep_sec)
			if ( not hours or now.hour in hours ) and ( not minutes or now.minute in minutes ):
				Log.info(f'Checking for new remote files')
				self.download()
				logger.check_size()
			sleep(delay)

if __name__ == '__main__':	# start here if called as application
	default_config_path = Path(__file__).with_suffix('.conf')
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-c', '--config',
		type = Path,
		help = f'Set path to config file (default: {default_config_path})',
		metavar = 'FILE',
		default = default_config_path
	)
	argparser.add_argument('-l', '--loglevel',
		type = str,
		help = 'Log level: debug, info (default), warning, error or critical',
		metavar = 'STRING',
		choices= ['debug', 'info', 'warning', 'error', 'critical'],
		default = 'debug'
	)
	argparser.add_argument('-s', '--simulate',
		action = 'store_true',
		help = 'Simulate: connect to server and list file, do not download any data',
	)
	args = argparser.parse_args()
	logger = Log('debug') if args.simulate else Log(args.loglevel)
	config_none = ('', 'none', 'no', 'false', '0')
	try:
		config = ConfigParser()
		config.read(args.config)
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
		Path(config['LOCAL'].get('download')),
		Path(config['LOCAL'].get('destination')),
		password = config['REMOTE'].get('password'),
		timeout = config['REMOTE'].getint('timeout'),
		retries = config['REMOTE'].getint('retries'),
		delay = config['REMOTE'].getint('delay'),
		decryptor = decryptor
	)
	if Log.debugging():
		if args.simulate:
			Log.info('Starting fetching remote structure')
			for path in collector.find(name=name):
				Log.info(f'{path}')
		else:
			Log.info('Starting download on debug level now and for once')
			collector.download(name=name)
		Log.info('Done')
		exit(0)
	def parse(string):
		if string.lower() in ('', 'all', 'every', 'each', '*', '.'):
			return
		return [int(i) for i in string.split(',')]
	Log.info('Starting main loop')
	try:
		collector.loop(logger,
			hours = parse(config['LOOP'].get('hours', '')),
			minutes = parse(config['LOOP'].get('minutes', '')),
			delay = config['LOOP'].getint('delay'),
			clean = config['LOOP'].get('clean'),
			keep = config['LOOP'].getint('keep', 0)
		)
	except KeyboardInterrupt:
		print()
		Log.info('Main loop terminated by Ctrl-C')
	exit(0)
