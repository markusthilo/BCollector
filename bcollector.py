#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.3.0_2025-11-25'
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
		match = None,
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
			self._downloader = HTTPDownloader(url, match=match, retries=retries, delay=delay)
		elif protocol == 'sftp':
			self._downloader = SFTPDownloader(url, password, match=match, timeout=timeout, retries=retries, delay=delay)
		else:
			raise ValueError(f'Unknown protocol {protocol}')

	def download(self):
		'''Download files'''
		for filename in set(self._downloader.ls()) - set(self._local.ls_download()):
			download_path = self._downloader.download(filename, self._local._download_path)
			if download_path:
				Log.info(f'Downloaded {download_path}')
				try:
					path = self._local.forward(filename)
				except:
					Log.error('Exception while forwarding {filename}')
				else:
					if path:
						Log.info(f'Created {path}')

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
	args = argparser.parse_args()
	logger = Log(args.loglevel)
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
	match = config['REMOTE'].get('match', '')
	match = match if not match.lower() in config_none else None
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
		match = match,
		password = config['REMOTE'].get('password'),
		timeout = config['REMOTE'].getint('timeout'),
		retries = config['REMOTE'].getint('retries'),
		delay = config['REMOTE'].getint('delay'),
		decryptor = decryptor
	)
	if Log.debugging():
		Log.info('Starting download on debug level now and for once')
		collector.download()
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
