#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime

class Backup:
	'''Handle the backup'''

	def __init__(self, path, keep):
		'''Create object for the backup directory'''
		self._path= path
		self._keep = keep

	def ls(self):
		'''List files in backup directory'''
		return (path for path in self.path.glob('*.zip.pgp'))

	def get_expired(self):
		'''Get the files that were created before given time delta'''
		oldest = datetime.timestamp(datetime.now()) - self._keep
		return (path for path in self.ls() if path.stat().st_mtime < oldest)

	def purge(self):
		'''Delete all files in backup directory that are expired'''
		for path in self.get_expired():
			try:
				path.unlink()
			except Exception as e:
				msg = f'Unable to remove expired file {path}:\n{e}'
				logging.error(msg)
				msg = f'ERROR: {msg}'
			else:
				msg = f'Removed expired file {path}'
				logging.info(msg)
				msg = f'INFO: {msg}'
			if logging.root.level == logging.DEBUG:
				print(msg)
