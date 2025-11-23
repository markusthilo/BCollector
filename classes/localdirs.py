#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from classes.logger import Logger as Log

class LocalDirs:
	'''Handle the backup'''

	def __init__(self, download_path, destination_path, decryptor=None):
		self._download_path = download_path
		self._destination_path = destination_path
		self._decryptor = decryptor

	def ls_download(self):
		'''List files in download directory'''
		for path in self._download_path.iterdir():
			if path.is_file():
				yield path.name

	def clean_download(self, keep):
		'''Delete all files in download directory that are expired'''
		for path in self._download_path.iterdir():
			if not path.is_file() and path.stat().st_mtime < oldest:
				try:
					path.unlink()
				except:
					Log.error(f'Unable to remove expired directory {path}')

	def forward(self, filename):
		'''Forward file from download to destination'''
		if self._decryptor:
			return self._decryptor.decrypt(self._download_path / filename, self._destination_path)
		else:
			try:
				destination_path = self._destination_path / filename
				destination_path.write_bytes(self._download_path.joinpath(filename).read_bytes())
				return destination_path
				### this is for python  >= 3.14 ###
				#return self._download_path.joinpath(filename).copy_into(self._destination_path)
			except:
				Log.error(f'Unable to copy {filename} to {self._destination_path}')
