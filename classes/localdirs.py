#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import getpid, getlogin
from socket import gethostname
from datetime import datetime
from classes.logger import Logger as Log

class LocalDirs:
	'''Handle the backup'''

	def __init__(self, download_dir_path, destination_dir_path, decryptor=None, trigger=None):
		self.download_path = download_dir_path
		self.destination_path = destination_dir_path
		self._decryptor = decryptor
		if trigger:
			self._trigger_path = trigger
			self._id = f'host: {gethostname()}\nuser: {getlogin()}\npid: {getpid()}'
		else:
			self._trigger_path = None
			self._id = None

	def mk_download_dir(self, relative_file_path):
		'''Create download directory'''
		download_dir_path = self.download_path.joinpath(relative_file_path).parent
		try:
			download_dir_path.mkdir(parents=True, exist_ok=True)
		except:
			Log.error(f'Unable to create download directory {download_dir_path}')
		return download_dir_path

	def forward(self, relative_path):
		'''Forward file from download to destination'''
		download_file_path = self.download_path.joinpath(relative_path)
		destination_file_path = self.destination_path.joinpath(relative_path)
		try:
			destination_file_path.parent.mkdir(parents=True, exist_ok=True)
		except:
			Log.error(f'Unable to create destination directory {destination_file_path.parent}')
			return
		if self._decryptor and self._decryptor.suffix_match(download_file_path):
			destination_file_path = self._decryptor.decrypt(download_file_path, self.destination_path)
			if destination_file_path:
				Log.info(f'Decrypted {download_file_path} to {destination_file_path}')
				return destination_file_path
		try:
			if destination_file_path.exists():
				Log.warning(f'File {destination_file_path} already exists,skipping copy attempt')
				return
			### this is for python < 3.14 ###
			destination_file_path.write_bytes(download_file_path.read_bytes())
			### this works for python  >= 3.14 ###
			# download_file_path.copy(destination_file_path)
			return destination_file_path
		except:
			Log.error(f'Unable to copy {download_file_path} to {self.destination_path}')

	def write_trigger(self):
		'''Write trigger file for download file'''
		if self._trigger_path:
			try:
				self._trigger_path.write_text(self._id, encoding='utf8')
			except:
				Log.error(f'Unable to create trigger file {self._trigger_path}')
			else:
				Log.info(f'Wrote trigger file {self._trigger_path}')
				return self._trigger_path

	def clean_download(self, relative_paths):
		'''Delete all given files in download directory'''
		dirs = dict()
		deleted = list()
		for relative_path in relative_paths:
			path = self.download_path.joinpath(relative_path)
			if path.is_dir():
				dirs[path] = len(path.parents)
			if path.is_file():	# remove file
				try:
					path.unlink()
				except:
					Log.error(f'Unable to remove file {path}')
				else:
					deleted.append(relative_path)
					Log.info(f'Removed file {path}')
		for path in sorted(dirs, key=dirs.get, reverse=True):	# remove empty directory
			if not any(path.iterdir()):
				try:
					path.rmdir()
				except:
					Log.error(f'Unable to remove directory {path}')
		return deleted