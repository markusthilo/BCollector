#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from paramiko import SSHClient, AutoAddPolicy
from time import sleep
from re import compile as re_compile
from stat import S_ISDIR
from classes.logger import Logger as Log

class SFTPDownloader:
	'Tools to fetch files via SFTP'

	def __init__(self, url, pw, timeout=None, retries=None, delay=None):
		'Initialze object and connect to server'
		self._root, _, user_host_port, sub = url.split('/', 3)
		self._path = Path(sub)
		try:
			user, host_port = user_host_port.split('@', 1)
		except ValueError:
			user, host_port = '', user_host_port
		try:
			host, port = host_port.split(':', 1)
		except ValueError:
			host, port = host_port, 22
		self._root += f'//{user_host_port.rstrip("/")}/'
		self._timeout = timeout if timeout else 30
		self._retries = retries if retries else 10
		self._delay = delay if delay else 2
		self.dirs = list()
		self.files = list()
		try:
			self._ssh = SSHClient()
			self._ssh.set_missing_host_key_policy(AutoAddPolicy())
			self._ssh.connect(hostname=host, port=port, username=user, password=pw, timeout=timeout)
			self._sftp = self._ssh.open_sftp()
		except Exception as ex:
			Log.error(message=f'Unable to connect to {host}:{port} as {user}', exception=ex)

	def iterdir(self, path):
		'''Iterate over remote directory'''
		path_str = f'{path}'.replace('\\', '/')
		for attempt in range(1, self._retries+1):
			try:
				items = self._sftp.listdir_attr(path_str)
			except:
				if attempt < self._retries:
					Log.debug(f'Attempt {attempt} to retieve {self._root}{path_str} failed, retrying in {self._delay} seconds')
					sleep(self._delay)
				else:
					raise OSError(f'Unable to retrieve file list from {self._root}{path_str}')
					return list(), list()
		dirs = list()
		files = list()
		for item in items:
			if S_ISDIR(item.st_mode):
				dirs.append(path / item.filename)
			else:
				files.append(path / item.filename)
		self.dirs.extend(dirs)
		self.files.extend(files)
		for dir_path in dirs:
			dirs, files = self.iterdir(dir_path)
		return dirs, files

	def find(self, name=None):
		'''List remote files'''
		try:
			self.iterdir(self._path)
		except Exception as ex:
			Log.error(exception=ex)
		else:
			if name:
				regex = re_compile(name)
				for path in self.files:
					if regex.match(path.name):
						yield path
			else:
				for path in self.files:
					yield path

	def download(self, remote_file_path, local_dir_path):
		'''Download file'''
		local_file_path = local_dir_path / remote_file_path
		remote_file_str = f'{remote_file_path}'.replace('\\', '/')
		Log.info(f'Downloading {remote_file_str} to {local_dir_path}')
		for attempt in range(1, self._retries + 1):
			try:
				self._sftp.get(remote_file_str, f'{local_file_path}')
			except:
				if attempt < self._retries:
					Log.debug(f'Attempt {attempt} of {self._retries} to retrieve {remote_file_str} failed, retrying in {self._delay} seconds')
					sleep(self._delay)
				else:
					Log.error(f'Unable to download {remote_file_str}')
			else:
				Log.debug(f'Received file {local_file_path}')
				return local_file_path

	def __del__(self):
		'''Close SFTP connection'''
		try:
			self._sftp.close()
			self._ssh.close()
		except:
			Log.error('Unable to close SFTP connection')
