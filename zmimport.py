#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.1_2021-12-22'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Fetch gpg encrypted files, save them on backup and export to target'

import logging
from os import listdir, remove, path
from shutil import copy2 as copyfile
from pathlib import Path
from hashlib import sha256
from sys import stdout, stderr
from re import match, sub
from subprocess import Popen, PIPE
from time import sleep
from datetime import datetime
from configparser import ConfigParser
from csv import DictReader, DictWriter
from csv import writer as SequenceWriter
from argparse import ArgumentParser, FileType

class Logger:
	'Logging for this tool'

	def __init__(self, level, filename, handlers=[logging.StreamHandler(stdout)]):
		'Initiate logging by given level and to given file'
		logging.basicConfig(
			level={
				'debug': logging.DEBUG,
				'info': logging.INFO,
				'warning': logging.WARNING,
				'error': logging.ERROR,
				'critical': logging.CRITICAL
			}[level],
			#filename = filename,
			stream = stdout,
			format = '%(asctime)s %(levelname)s: %(message)s',
			datefmt = '%Y-%m-%d %H:%M:%S'
		)
		#logging.getLogger().addHandler(logging.StreamHandler(stream=stdout))
		#if handlers != None:
		#	for handler in handlers:
		#		logging.getLogger().addHandler(handler)
		#logging.info(f'Start logging to {filename}')
		#stderr.write = self.__handler_stderr__
		self.filename = filename	# log to file when used in the real world

	def __handler_stderr__(self, stream):
		'Handle write stream from stderr'
		if stream != '\n':
			logger.error(stream)

class Config:
	'Handle the config file'

	def __init__(self, configfile):
		'Get configuration from file and initiate logging'
		if configfile == None:
			configfile = Path(path.dirname(__file__)) / 'zmimport.conf'
		config = ConfigParser()
		config.read(configfile)
		self.loglevel = config['LOGGING']['level']
		self.logfile = Path(config['LOGGING']['filepath'])
		self.sourcepath = Path(config['PLACES']['sourcepath'])
		self.targetpath = Path(config['PLACES']['targetpath'])
		self.backuppath = Path(config['PLACES']['backuppath'])
		self.csvpath = Path(config['FILELIST']['filepath'])
		self.pgp_cmd = Path(config['PGP']['command'])
		self.triggerfile = Path(config['TRIGGER']['filepath'])
		self.updates = [ t.strip(' ') for t in config['TRIGGER']['time'].split(',') ]
		self.sleep = config['TRIGGER']['sleep']

class PGPDecoder:
	'Use command line PGP/GPG to decode'

	def __init__(self, cmd):
		'Create decoder by giving the command line'
		self.cmd = cmd

	def decode(self, encrypted, destdir):
		'Decode pgp file and return generated file'
		outfile = destdir / encrypted.stem
		process = Popen((self.cmd, '--output', outfile, '--decrypt', encrypted))
		process.wait()
		if process.returncode == 0:
			return outfile
		logging.error(f'Could not decrypt {encrypted} to {outfile}')
		raise RuntimeError('Decoder returned error')

class FileOperations:
	'Collection of basic file operations'

	def __init__(self, dirpath):
		'Set source path'
		self.path = dirpath

	def ls(self):
		'List source files as set'
		return set(listdir(self.path))

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

class Source(FileOperations):
	'Source to import from'

	def fetch(self, sourcefile, dstpath):
		'Copy one file to given file (backup server is intended)'
		sourcepath = self.fullpath(sourcefile)
		copyfile(sourcepath, dstpath)
		filepath = dstpath / sourcefile
		sourcesum = self.sha256(sourcepath)
		filesum = self.sha256(filepath)
		logging.debug(
			f'Copied {sourcepath} (checksum: {sourcesum}) to {filepath} (checksum: {filesum})'
		)
		if sourcesum == filesum:
			return sourcepath, filepath, filesum, self.now()
		remove(filepath)
		logging.error(f'Could not copy {sourcepath} to {filepath}, removing {filepath}')
		raise RuntimeError('Checksum mismatch on fetching file(s) from source')

class Target(FileOperations):
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

class Backup(FileOperations):
	'Backup to keep the files'

	def __init__(self, dirpath, csvpath):
		'Create object for work on the backup server'
		super().__init__(dirpath)
		self.csvpath = csvpath
		self.fetched = set()	# already fetched from source
		self.putted = set()	# already putted to target
		self.fieldnames = ('filename_orig', 'sum_orig', 'ts_fetch', 'filename_dec', 'sum_dec', 'ts_put')
		if csvpath.exists():	# check if filelist exists and has matching fieldnames
			with open(csvpath, 'r') as f:
				reader = DictReader(f, fieldnames=self.fieldnames)
				fieldnames = tuple(next(reader).values())	# read headline
				logging.debug(
					f'{csvpath} stores the following fields: '
					+ str(fieldnames).lstrip('(').rstrip(')')
				)
				if fieldnames != self.fieldnames:	# check for wrong csv file format
					logging.error(
						f'{csvpath} contains mismatching fieldnames: '
						+ str(fieldnames).lstrip('(').rstrip(')')
					)
					raise RuntimeError('Mismatching fieldnames in CSV file')
				for row in reader:	# get the already handled files from csv file
					print(row)
					self.fetched.add(row['filename_orig'])
					self.putted.add(row['filename_dec'])
		else:	# creste csv file if not existend
			with open(csvpath, 'w', newline='') as f:
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
		self.decoder = PGPDecoder(config.pgp_cmd)
		self.source = Source(config.sourcepath)
		logging.debug(f'Source is {config.sourcepath}')
		self.target = Target(config.targetpath)
		logging.debug(f'Target is {config.targetpath}')
		self.backup = Backup(config.backuppath, config.csvpath)
		logging.debug(f'Backup is {config.backuppath}')
		logging.debug(f'Files / transfers will be stored in {config.csvpath}')
		newfiles = list()
		for new in self.__fetchnew__():
			targetpath, targetsum, ts_put = self.target.put(self.backup.path / new['filename_dec'])
			self.backup.remove(new['filename_dec'])
			newfiles.append({
				'filename_orig': new['filename_orig'],
				'sum_orig': new['sum_orig'],
				'ts_fetch': new['ts_fetch'],
				'filename_dec': new['filename_dec'],
				'sum_dec': targetsum,
				'ts_put': ts_put
			})
		if newfiles != list():
			self.backup.update_csv(newfiles)

	def __fetchnew__(self):
		'Fetch new files from source'
		newonsource = self.source.ls() - self.backup.fetched	# filter for new files
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
				yield {
					'filename_orig': sourcefile,
					'sum_orig': sum_orig,
					'ts_fetch': ts_fetch,
					'filename_dec': decodedpath.name,
				}

class MainLoop:
	'Main loop waiting for triggers'

	def __init__(self, config):
		'Initiate main loop'
		print(config.triggerfile)
		print(config.updates)
		print(config.sleep)
		print(datetime.now().strftime('%H:%M'))
		while True:	# check if trigger file exists or time matches
			if config.triggerfile.exists():
				remove(config.triggerfile)
				Transfer(config)
			elif datetime.now().strftime('%H:%M') == config.updates:
				Transfer(config)
		else:
			sleep(config.sleep)

if __name__ == '__main__':	# start here if called as application
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-c', '--config', type=FileType('rt', encoding='utf8'),
		help='Config file', metavar='FILE'
	)
	args = argparser.parse_args()
	config = Config(args.config)
	log = Logger(config.loglevel, config.logfile)
	MainLoop(config)
