#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.3.0_2025-11-25'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Sync remote and local files. HTTP and SFTP are possible protocols. Forward to final destination, decrypt gpg encrypted files.'

from time import sleep
from datetime import datetime
from argparse import ArgumentParser
from pathlib import Path
from configparser import ConfigParser
from sys import exit
from classes.config import Config
from classes.logger import Logger as Log
from classes.httpdownloader import HTTPDownloader
from classes.sftpdownloader import SFTPDownloader
from classes.pgpdecryptor import PGPDecryptor
from classes.backup import Backup

class BCollector:
	'''Sync loacl with remote'''

	def __init__(self, url, download_path, destination_path,
		password = '',
		timeout = 30,
		retries = 10,
		delay = 2,
		decryptor = None
	):
		'''Definitions'''
		self._url = url.rstrip('/')
		#try:
		#	protocol, _, host_port, sub = url.split('/', 3)
		#	host, port = f'{host_port}:'.split(':', 1)
		#	port = int(port.rstrip(':')) if port else None
		#except:
		#	Log.critical(f'Unable to parse {url}')
		#print(url, sub)
		protocol = self._url.split(':', 1)[0].lower()
		if protocol == 'http':
			self._downloader = HTTPDownloader(url, retries=retries, delay=delay)
		elif protocol == 'sftp':
			self._downloader = SFTPDownloader(url, password, timeout=timeout, retries=retries, delay=delay)
		else:
			raise ValueError(f'Unknown protocol {protocol}')

	def ls(self):
		'''List remote directory / links in site'''
		return tuple(self._downloader.ls())

	def download(self):
		'''Download files'''
		local_filenames = [path.name for path in self._backup.ls()]
		remote_filenames = downloader.ls()
		if not remote_filenames:
			return
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

	def loop(self, logger, hours=None, minutes=[0, 15, 30, 45], delay=10, keep=None):
		'''Endless loop for daemon mode'''

		'''
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
		'''

if __name__ == '__main__':	# start here if called as application
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-c', '--config',
		type = Path,
		help = 'Set path to config file',
		metavar = 'FILE',
		default = Path(__file__).with_suffix('.conf')
	)
	argparser.add_argument('-l', '--loglevel',
		type = str,
		help = 'Log level: debug, info (default), warning, error or critical',
		metavar = 'STRING',
		choices= ['debug', 'info', 'warning', 'error', 'critical'],
		default = 'info'
	)
	args = argparser.parse_args()
	logger = Log(args.loglevel)
	try:
		config = ConfigParser()
		config.read(args.config)
	except:
		Log.critical(f'Unable to read config file {args.config}')
	try:
		log_path = Path(config['LOCAL']['logfile'])
	except:
		Log.critical(f'Unable to create log file')
	try:
		remote_keys = tuple(config['REMOTE'])
	except:
		Log.critical(f'Missing REMOTE section in {args.config}')
	password = config['REMOTE']['password'] if 'password' in remote_keys else ''
	regex = config['REMOTE']['regex'] if 'regex' in remote_keys else None
	timeout = int(config['REMOTE']['timeout']) if 'timeout' in remote_keys else 30
	if 'encryption' in remote_keys:
		encryption = config['REMOTE']['encryption'].lower()
		if encryption in ('none', 'no', 'false', '0'):
			decryptor = None
		elif encryption in ('pgp', 'gpg'):
			try:
				decryptor = PGPDecryptor(config['REMOTE']['passphrase'])
			except:
				Log.critical(f'Unable to setup decryptor for {encryption}')
		else:
			Log.critical(f'Unknown encryption: {encryption}')
	collector = BCollector(
		config['REMOTE']['url'],
		Path(config['LOCAL']['download']),
		Path(config['LOCAL']['destination']),
		password = password,
		timeout = timeout,
		retries = int(config['REMOTE']['retries']),
		delay = int(config['REMOTE']['delay']),
		decryptor = decryptor
	)

	### DEBUG ###
	for item in collector.ls():
		print(item)
	exit(0)
	#############

	if Log.debugging():
		Log.info('Starting download on debug level now and for once')
		collector.download()
		exit(0)
	try:
		keep = int(config['LOCAL']['keep']) * 2629746	# time delta in seconds to keep files
	except:
		keep = None
	def parse(string):
		if string.lower() in ('all', 'every', 'each', '*', '.'):
			return
		return [int(i) for i in string.split(',')]
	try:
		hours = parse(config['LOOP']['hours'])
		minutes = parse(config['LOOP']['minutes'])
		delay = int(config['LOOP']['delay'])
	except:
		Log.critical('Unable to parse loop configuration')
	Log.info('Starting main loop')
	try:
		collector.loop(logger, hours=hours, minutes=minutes, delay=delay, keep=keep)
	except KeyboardInterrupt:
		Log.info('Main loop terminated by Ctrl-C')
	exit(0)
