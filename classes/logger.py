#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from traceback import format_tb, format_exc
from sys import stdout, exc_info, exit
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED

class Logger:
	'Advanced logging functionality'

	@staticmethod
	def translate(level):
		'''Translate string to logging level'''
		return logging.__dict__[level.upper()] if isinstance(level, str) else level

	def get_level():
		'''Get current log level'''
		return logging.root.level

	@staticmethod
	def debugging():
		'''Return True if root log level is DEBUG or lower'''
		return Logger.get_level() <= logging.DEBUG

	@staticmethod
	def exception(level, message=None):
		'''Log exception'''
		ex_type, ex_text, traceback = exc_info()
		if ex_type:
			msg = f'{message}, {ex_type.__name__}: {ex_text}' if message else f'{ex_type.__name__}: {ex_text}'
		else:
			msg = message if message else ''
		if Logger.debugging() and traceback:
			msg += f'\n{format_exc().strip()}'
		logging.__dict__[level.lower()](msg)

	@staticmethod
	def debug(msg):
		'''Print debug message'''
		logging.debug(msg)

	@staticmethod
	def info(msg):
		'''Print info message'''
		logging.info(msg)

	@staticmethod
	def warning(message=None):
		'''Log warning'''
		Logger.exception('warning', message=message)

	@staticmethod
	def error(message=None, exception=None):
		'''Log error'''
		Logger.exception('error', message = message)

	@ staticmethod
	def critical(message=None, exception=None):
		'''Log critical error'''
		Logger.exception('critical', message=message)
		exit(1)

	def __init__(self, level='debug'):
		'''Define logging by given level and to given file'''
		self.level = self.translate(level)
		self._logger = logging.getLogger()
		self._logger.setLevel(self.level)
		self._stream_handler = logging.StreamHandler(stdout)
		self._stream_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
		self._logger.addHandler(self._stream_handler)
		self._file_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
		self.path = None
	
	def add_file(self, path):
		'''Create logfile and zip old if exists'''
		self.rotate()
		if path.is_file():
			with ZipFile(path.with_suffix(datetime.now().strftime('.%Y-%m-%d_%H%M%S.zip')), 'w', ZIP_DEFLATED) as zf:
				zf.write(path, path.name)
		elif path.exists():
			raise FileExistsError(f'{path} is not a file')
		self.path = path
		self._file_handler = logging.FileHandler(mode='w', filename=self.path)
		self._file_handler.setFormatter(self._file_formatter)
		self._logger.addHandler(self._file_handler)
		self.debug(f'Start logging to {self.path}')

	def rotate(self):
		'''Rotate and backup old logfile as zip'''
		if self.path:
			self._file_handler.close()
			self.add_file(self.path)
