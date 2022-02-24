#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.1_2022-02-15'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Deliver files to folders'

import logging
from shutil import move
from pathlib import Path
from hashlib import sha256
from sys import stdout, stderr
from sys import exit as sysexit
from datetime import datetime
from configparser import ConfigParser
from csv import DictReader
from argparse import ArgumentParser, FileType

class Config:
	'Handle the config file'

	def __init__(self, configfile):
		'Get configuration from file and initiate logging'
		if configfile == None:
			configfile = Path(path.dirname(__file__)) / 'beeftraeger.conf'
		config = ConfigParser()
		config.read(configfile)
		self.sourcedir = Path(config['SOURCE']['path'])
		self.targetbase = Path(config['TARGET']['base'])
		self.targetpattern = config['TARGET']['pattern']

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

	def now(self):
		'Give timestamp for now'
		return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

class Tar(FileOperations):
	'Target to copy the files to'

	def put(self, filepath):
		'Copy one file to target'
		copyfile(filepath, self.path)
		targetpath = self.fullpath(filepath.name)
		filesum = self.sha256(filepath)
		targetsum = self.sha256(targetpath)
		logging.debug(
			f'Copied {filepath} (checksum: {filesum}) to {targetpath} (checksum: {targetsum})'
		)
		if filesum == targetsum:
			return targetpath, targetsum, self.now()
		remove(targetpath)
		logging.error(f'Could not copy {filepath} to {targetpath}, removing {targetpath}')
		raise RuntimeError('Checksum mismatch on putting file(s) to target')

class CSV:
	'Backup to keep the files'

	FILEDNAMES = ('identifier', 'target')

	def __init__(self, csvfile):
		'Create object for work on the backup server'
		with open(csvfile, 'r') as f:
				reader = DictReader(f, fieldnames=self.FIELDNAMES)
				fieldnames = tuple(next(reader).values())	# read headline
				if fieldnames != self.FIELDNAMES:	# check for wrong csv file format
					raise RuntimeError(
						f'{csvpath} contains mismatching fieldnames: '
						+ str(fieldnames).lstrip('(').rstrip(')')
					)
				
				for row in reader:	# get the already handled files from csv file
					yield ( {fn: row[fn]} for fn in fieldnames)
						



class Transfer:
	'Functionality to process the whole file transfer'

	def __init__(self, config):
		'File transfer'
		try:
			self.decoder = PGPDecoder(config.pgp_cmd, config.pgp_passphrase)
			logging.debug(f'File / transfer infos will be stored in {config.csvpath}')
			self.source = Source(config.sourcepath, config.sourcetype, config.xpath)
			logging.debug(f'Source is {config.sourcepath}')
			self.backup = Backup(config.backuppath, config.csvpath)
			logging.debug(f'Backup is {config.backuppath}')
			for path, pattern in config.targets.items():
				logging.debug(f'Target is {path} for regex pattern "{pattern}"')
			logging.debug(f'Basic target is {config.targetpath}')
			newfiles = list()
			for filename_orig, sum_orig, ts_fetch, filename_dec in self.__fetchnew__():
				targetdir = None
				for path, pattern in config.targets.items():
					if match(pattern, filename_orig) != None:
						targetdir = path
						break
				if targetdir == None:
					targetdir = config.targetpath
				logging.debug(f'{filename_dec} will be moved to {targetdir}')
				target = Target(targetdir)
				targetpath, targetsum, ts_put = target.put(self.backup.path / filename_dec)
				self.backup.remove(filename_dec)
				newfiles.append({
					'filename_orig': filename_orig,
					'sum_orig': sum_orig,
					'ts_fetch': ts_fetch,
					'filename_dec': filename_dec,
					'sum_dec': targetsum,
					'ts_put': ts_put
				})
			if newfiles != list():
				self.backup.update_csv(newfiles)
		except Exception as e:
			logging.error(e)
		if logging.root.level != logging.DEBUG:
			sleep(60)	# wait one minute to make shure not to fetch again at same time

	def __fetchnew__(self):
		'Fetch new files from source'
		newonsource = self.source.listfiles() - self.backup.fetched	# filter for new files
		if newonsource == set():
			logging.info(f'Did not find new file(s) on {self.source.path}')
			return
		else:
			logging.info(
				f'Found new file(s) on {self.source.path}: '
				+ str(newonsource).lstrip('{').rstrip('}')
			)
			fetches = list()	# to store the new files / fetching procedures
			for sourcefile in newonsource:
				sourcepath, backuppath, sum_orig, ts_fetch = self.source.fetch(sourcefile, self.backup.path)
				logging.info(f'Copied {sourcepath} to {backuppath}')
				decodedpath = self.decoder.decode(backuppath, self.backup.path)
				logging.info(f'Decoded {backuppath} to {decodedpath}')
				yield sourcefile, sum_orig, ts_fetch, decodedpath.name

if __name__ == '__main__':	# start here if called as application
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-c', '--config', type=FileType('rt', encoding='utf8'),
		help='Config file', metavar='FILE'
	)
	args = argparser.parse_args()
	config = Config(args.config)
	log = Logger(config.loglevel, config.logfile)
	if logging.root.level == logging.DEBUG:
		logging.info('Starting file transfer on debug level now and for once')
		Transfer(config)
		sysexit(0)
	else:
		MainLoop(config)
