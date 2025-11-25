#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from classes.logger import Logger as Log

class LocalDirs:
	'''Handle the backup'''

	def __init__(self, download_dir_path, destination_dir_path, decryptor=None):
		self._download_path = download_dir_path
		self._destination_path = destination_dir_path
		self._decryptor = decryptor

	def rglob_download(self):
		'''List files in download directory'''
		for path in self._download_path.rglob('*'):
			if path.is_file():
				yield path.relative_to(self._download_path)

	def clean_download(self, keep):
		'''Delete all files in download directory that are expired'''
		dirs = dict()
		for path in self._download_path.rglob('*'):
			if path.is_dir():
				dir[path] = len(path.parents)
			if path.is_file() and path.stat().st_mtime < oldest:	# remove expired file
				try:
					path.unlink()
				except:
					Log.error(f'Unable to remove expired file {path}')
		for path in sorted(dirs, key=dirs.get, reverse=True):	# remove empty directory
			if not any(path.iterdir()):
				try:
					path.rmdir()
				except:
					Log.error(f'Unable to remove empty directory {path}')

	def mk_download_dir(self, relative_file_path):
		'''Create download directory'''
		download_dir_path = self._download_path.joinpath(relative_file_path).parent
		try:
			download_dir_path.mkdir(parents=True, exist_ok=True)
		except:
			Log.error(f'Unable to create download directory {download_dir_path}')
		return download_dir_path

	def forward(self, download_file_path):
		'''Forward file from download to destination'''
		destination_file_path = self._destination_path.joinpath(download_file_path.relative_to(self._download_path))
		try:
			destination_file_path.parent.mkdir(parents=True, exist_ok=True)
		except:
			Log.error(f'Unable to create destination directory {destination_file_path.parent}')
			return
		if self._decryptor.suffix_match(download_file_path):
			destination_file_path = self._decryptor.decrypt(download_file_path, self._destination_path)
			if destination_file_path:
				Log.info(f'Decrypted {download_file_path} to {destination_file_path}')
				return destination_file_path
		try:
			destination_file_path.write_bytes(download_file_path.read_bytes())
			### this is for python  >= 3.14 ###
			#return self._download_path.copy_into(self._destination_file_path)
		except:
			Log.error(f'Unable to copy {download_file_path} to {self._destination_path}')
		else:
			return destination_file_path
