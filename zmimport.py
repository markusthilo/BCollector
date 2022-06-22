#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.2_2022-06-22'
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

class Logger:
	'Logging for this tool'

	def __init__(self, level, filename):
		'Initiate logging by given level and to given file'
		logging.basicConfig(
			level={
				'debug': logging.DEBUG,
				'info': logging.INFO,
				'warning': logging.WARNING,
				'error': logging.ERROR,
				'critical': logging.CRITICAL
			}[level],
			filename = filename,
			format = '%(asctime)s %(levelname)s: %(message)s',
			datefmt = '%Y-%m-%d %H:%M:%S'
		)
		logging.info(f'Start logging to {filename}')
		self.filename = filename	# log to file

class Config:
	'Handle the config file'

	def __init__(self, configfile=Path(__file__).parent / 'zmimport.conf'):
		'Get configuration from file and initiate logging'
		config = ConfigParser()
		config.read(configfile)
		self.loglevel = config['LOGGING']['level']
		self.logfile = Path(config['LOGGING']['filepath'])
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

class PGPDecoder:
	'Use command line PGP/GPG to decode'

	def __init__(self, cmd, passphrase):
		'Create decoder by giving the command line'
		self.cmd = cmd
		self.passphrase = passphrase

	def decode(self, encrypted, destdir):
		'Decode pgp file and return generated file'
		outfile = destdir / encrypted.stem
		pcmd = (
				self.cmd,
				'--pinentry-mode=loopback',
				'--passphrase', self.passphrase,
				'--output', outfile,
				'--decrypt', encrypted
		)
		logging.debug(f'Now executing: {pcmd}')
		process = Popen(pcmd, stdout = PIPE, stderr = STDOUT)
		while process.poll() is None:
			while True:
				err = process.stdout.readline().decode().strip()
				if err:
					logging.info(err)
				else:
					break
		if process.returncode == 0:
			return outfile
		logging.error(f'Could not decrypt {encrypted} to {outfile}')
		raise RuntimeError('Decoder returned error')

class HttpFileTransfer:
	'Tools to fetch files via HTTP'

	def __init__(self, path, xpath):
		'Set source path'
		self.path = path
		self.xpath = xpath

	def basedir(self, retries=10, delay=2):
		'List source files as set'
		for at in range(1, retries+1):
			try:
				landing = parse_html(self.path)
				logging.debug(f'Received {self.path} on attempt {at}')
				return ( filename for filename in landing.xpath(self.xpath) )
			except OSError:
				logging.error(f'Attempt {at} of {retries} to retrieve {self.path} failed')
				sleep(delay)
		logging.error(f'Could not retrieve {self.path}')
		raise RuntimeError(f'Could not retrieve {self.path}')

	def download(self, filename, dstpath, retries=10, delay=2):
		'Download given file and generate sha256'
		sourcepath = self.path + filename
		filepath = dstpath / filename
		for at in range(1, retries+1):
			logging.debug(f'Attempt {at} downloading {sourcepath} to {dstpath}')
			with urlopen(sourcepath) as response:
				sourcefile = response.read()
			with open(filepath, 'wb') as filehandler:
				filelen = filehandler.write(sourcefile)
			if filelen == len(sourcefile):
				logging.debug(f'Building sha256 for {filename}')
				h = sha256()
				h.update(sourcefile)
				return sourcepath, filepath, h.hexdigest()
			logging.error(f'Source file has {len(sourcefile)} bytes but wrote {filelen} bytes')
		logging.error(f'Error while downloading {sourcepath}')
		raise RuntimeError(f'Error while downloading {sourcepath}')

class FileOperations:
	'Collection of basic file operations'

	def __init__(self, path):
		'Set path'
		self.path = path

	def ls(self):
		'List files as set'
		return ( f for f in self.path.iterdir() if f.is_file() )

	def fullpath(self, filename):
		'Return full path to given file'
		return self.path / filename

	def sha256(self, filepath):
		'Generate sha256 hash from file'
		logging.debug(f'Building sha256 from {filepath}')
		h = sha256()
		with open(filepath, 'rb') as f:
			while True:
				block = f.read(h.block_size)
				if not block:
					break
				h.update(block)
		return h.hexdigest()

	def rm(self, filename):
		'Remove file using self.path'
		remove(self.fullpath(filename))

	def now(self):
		'Give timestamp for now'
		return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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

class Transfer:
	'Functionality to process the whole file transfer'

	def __init__(self, config):
		'File transfer'
		decoder = PGPDecoder(config.pgp_cmd, config.pgp_passphrase)
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

class MainLoop:
	'Main loop waiting for triggers'

	def __init__(self, config):
		'Initiate main loop'
		self.config = config
		logging.info('Starting main loop')
		while True:	# check if trigger file exists or time matches
			if config.triggerfile.exists():
				remove(config.triggerfile)
				self.worker()
			elif datetime.now().strftime('%H:%M') in config.updates:
				self.worker()
				sleep(config.sleep)

	def worker(self):
		'Do the main work'
		try:
			Transfer(config)
		except Exception as e:
			logging.error(e)

if __name__ == '__main__':	# start here if called as application
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-c', '--config', type=Path,
		help='Config file', metavar='FILE',
		default=Path(__file__).parent / 'zmimport.conf'
	)
	args = argparser.parse_args()
	config = Config(configfile=args.config)
	log = Logger(config.loglevel, config.logfile)
	if logging.root.level == logging.DEBUG:
		logging.info('Starting file transfer on debug level now and for once')
		Transfer(config)
		sysexit(0)
	else:
		MainLoop(config)
