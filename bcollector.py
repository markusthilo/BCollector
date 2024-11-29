#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.1_2024-11-28'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Fetch gpg encrypted files, save them on backup and export to target'

import logging
from os import remove
from shutil import copy2 as copyfile
from pathlib import Path
from lxml.html import parse as parse_html
from urllib.request import urlopen
from hashlib import sha256
from sys import exit as sysexit
from re import match
from subprocess import Popen, PIPE, STDOUT
from time import sleep
from datetime import datetime
from configparser import ConfigParser
from csv import DictReader, DictWriter
from csv import writer as SequenceWriter
from argparse import ArgumentParser, FileType
### Custom Libraries ###
from lib.logger import Logger
from lib.httpdownloader import HttpDownloader
from lib.pgpdecoder import PgpDecoder

class Config:
	'Handle the config file'

	def __init__(self, path):
		'Get configuration from file and initiate logging'
		config = ConfigParser()
		config.read(path)
		self.logdir = Path(config['DIRS']['log'])
		self.csvpath = Path(config['FILELIST']['filepath'])
		self.fieldnames = [ fn.strip(' ') for fn in  config['FILELIST']['fieldnames'].split(',') ]
		self.pgp_cmd = Path(config['PGP']['command'])
		self.pgp_passphrase = config['PGP']['passphrase']
		self.triggerfile = Path(config['TRIGGER']['filepath'])
		self.updates = [ t.strip(' ') for t in config['TRIGGER']['time'].split(',') ]
		self.sleep = int(config['TRIGGER']['sleep'])
		if self.sleep < 60:	# or there will be several polls in one minute
			self.sleep = 60
		self.sourcetype = config['SOURCE']['type'].lower()
		self.sourcepath = Path(config['SOURCE']['path'])
		if self.sourcetype == 'url':
			self.sourcepath = config['SOURCE']['path']
			if self.sourcepath[-1] != '/':
				self.sourcepath += '/'
			self.xpath = config['SOURCE']['xpath']
			self.retries = int(config['SOURCE']['retries'])
			self.retrydelay = int(config['SOURCE']['delay'])
		else:
			self.sourcepath = Path(config['SOURCE']['path'])
			self.xpath = ''
		self.backuppath = Path(config['BACKUP']['path'])
		self.targets = dict()
		for section in config.sections():
			if section[:6] == 'TARGET':
				if section == 'TARGET':
					self.targetpath = Path(config['TARGET']['path'])
				else:
					self.targets[Path(config[section]['path'])] = config[section]['pattern']


class Backup(FileOperations):
	'Backup to keep the files'

	def __init__(self, config):
		'Create object for work on the backup server'
		super().__init__(config.backuppath)
		self.csvpath = config.csvpath
		self.fieldnames = config.fieldnames
		self.fetched = set()	# already fetched from source
		self.putted = set()	# already putted to target
		if self.csvpath.exists():	# check if filelist exists and has matching fieldnames
			with open(self.csvpath, 'r') as f:
				reader = DictReader(f)
				logging.debug(
					f'{self.csvpath} stores the following fields: '
					+ str(reader.fieldnames).lstrip('(').rstrip(')')
				)
				if self.fieldnames != reader.fieldnames:	# check for wrong csv file format
					logging.error(
						f'{csvpath} contains mismatching fieldnames: '
						+ str(reader.fieldnames).lstrip('(').rstrip(')')
					)
					raise RuntimeError('Mismatching fieldnames in CSV file')
				for row in reader:	# get the already handled files from csv file
					self.fetched.add(row['filename_orig'])
					self.putted.add(row['filename_dec'])
		else:	# creste csv file if not existend
			with open(self.csvpath, 'w', newline='') as f:
				writer = SequenceWriter(f)
				writer.writerow(self.fieldnames)

	def remove(self, filename):
		'Remove file from backup'
		filepath = self.fullpath(filename)
		self.rm(filepath)
		logging.debug(f'Removed {filepath}')

	def update_csv(self, newfiles):
		with open(self.csvpath, 'a', newline='') as f:	# open csv file to append new files / transfers
			writer = DictWriter(f, self.fieldnames)
			for row in newfiles:
				writer.writerow(row)
		logging.info(f'Updated {self.csvpath}')

class Collector:
	'Functionality to process the whole file transfer'

	def __init__(self, config):
		'File transfer'
		decoder = PgpDecoder(config.pgp_cmd, config.pgp_passphrase)

class Source(FileOperations, HttpFileTransfer):
	'Source to import from'

	def __init__(self, config):
		self.path = config.sourcepath
		self.sourcetype = config.sourcetype
		if self.sourcetype == 'url':
			self.xpath = config.xpath
			self.retries = config.retries
			self.delay = config.retrydelay

	def listfiles(self):
		'List files as set'
		logging.debug('Getting source file list')
		if self.sourcetype == 'url':
			return set( fn for fn in super().basedir(retries=self.retries, delay=self.delay) if fn[-4:] == '.pgp' )
		else:
			return set( f for f in super().ls() if f.suffix == '.pgp' )

	def fetch(self, sourcefile, dstpath):
		'Copy one file to given path (backup server is intended)'
		if self.sourcetype == 'url':
			sourcepath, filepath, filesum = self.download(sourcefile, dstpath)
		else:
			sourcepath = self.fullpath(sourcefile)
			filepath = dstpath / sourcefile
			copyfile(sourcepath, dstpath)
			sourcesum = self.sha256(sourcepath)
			filesum = self.sha256(filepath)
			logging.debug(
				f'Copied {sourcepath} (checksum: {sourcesum}) to {filepath} (checksum: {filesum})'
			)
			if sourcesum != filesum:
				remove(filepath)
				logging.error(f'Could not download / copy {sourcepath} to {filepath}, removing {filepath}')
				raise RuntimeError('Checksum mismatch on fetching file(s) from source')
		return sourcepath, filepath, filesum, self.now()




		logging.debug(f'File / transfer infos will be stored in {config.csvpath}')
		source = Source(config)
		logging.debug(f'Source is {source.path}')
		backup = Backup(config)
		logging.debug(f'Backup is {backup.path}')
		for path, pattern in config.targets.items():
			logging.debug(f'Target is {path} for regex pattern "{pattern}"')
		logging.debug(f'Basic target is {config.targetpath}')
		newonsource = source.listfiles() - backup.fetched	# filter for new files
		if newonsource == set():
			logging.info(f'Did not find new file(s) on {source.path}')
			return
		logging.info(
			f'Found new file(s) on {source.path}: '
			+ str(newonsource).lstrip('{').rstrip('}')
		)
		fetches = list()	# to store the fetched files
		for sourcefile in newonsource:
			sourcepath, backuppath, sum_orig, ts_fetch = source.fetch(sourcefile, backup.path)
			logging.info(f'Copied {sourcepath} to {backuppath}')
			fetches.append((Path(sourcefile).name, sum_orig, ts_fetch))
		decoded = list()	# to store the decoded files
		for filename_orig, sum_orig, ts_fetch in fetches:
			backuppath = backup.path / filename_orig
			targetdir = None	# select target directory
			for path, pattern in config.targets.items():
				if match(pattern, filename_orig) != None:
					targetdir = path
					break
			if targetdir == None:
				targetdir = config.targetpath
			try:
				decodedpath = decoder.decode(backuppath, targetdir)
				logging.info(f'Decoded {backuppath} to {decodedpath}')
			except RuntimeError:
				backup.remove(backuppath)
				continue
			targetsum = backup.sha256(decodedpath)
			decoded.append({
				'filename_orig': filename_orig,
				'sum_orig': sum_orig,
				'ts_fetch': ts_fetch,
				'filename_dec': decodedpath.name,
				'sum_dec': targetsum
			})
		if decoded != list():
			backup.update_csv(decoded)

class Worker:
	'''Do the work'''

	def __init__(self, config):
		'''Initiate main loop'''
		self.collector = Collector(config)
		self.sleep = config.sleep

	def run(self)
		'''Run one time for loglevel debug'''
		self.collector.run()

	def loop(self):
		'''Endless loop for doemon mode'''
		while True:
			try:
				self.collector.run()
			except Exception as e:
				logging.error(e)
			sleep(self.sleep)

if __name__ == '__main__':	# start here if called as application
	this_script_path = Path(__file__)
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-c', '--config',
		type = Path,
		help = 'Config file',
		metavar = 'FILE',
		default = this_script_path.with_suffix('conf')
	)
	argparser.add_argument('-l', '--loglevel',
		type = str,
		help = 'Log level',
		metavar = 'STRING',
		choices= ['debug', 'info', 'warning', 'error', 'critical']
		default = 'info'
	)
	args = argparser.parse_args()
	config = Config(args.config)
	Logger(level=args.loglevel, dir=config.logdir)
	worker = Worker(config)
	if logging.root.level == logging.DEBUG:
		logging.info('Starting download on debug level now and for once')
		worker.run()
		sysexit(0)
	else:
		logging.info('Starting main loop')
		worker.loop()
