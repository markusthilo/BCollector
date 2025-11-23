#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from classes.logger import Logger as Log

class Backup:
	'''Handle the backup'''

	def __init__(self, path):
		'''Create object for the backup directory'''
		self._path= path

	def ls(self, pattern='*'):
		'''Get files in backup directory'''
		return (path for path in self.path.glob(pattern))

	def get_expired(self, keep):
		'''Get the files that were created before given time delta'''
		oldest = datetime.timestamp(datetime.now()) - keep
		return (path for path in self.ls() if path.stat().st_mtime < oldest)

	def purge(self, keep):
		'''Delete all files in backup directory that are expired'''
		for path in self.get_expired(keep):
			try:
				path.unlink()
			except Exception as e:
				Log.error(f'Unable to remove expired file {path}')
			else:
				Log.info(f'Removed expired file {path}')
