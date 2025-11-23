#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from paramiko import SSHClient, AutoAddPolicy
from time import sleep
from re import match as re_match
from classes.logger import Logger as Log

class SFTPDownloader:
	'Tools to fetch files via SFTP'

	def __init__(self, url, pw, timeout=30, retries=10, delay=2):
		'Initialze object and connect to server'
		self._url = url if url[-1] == '/' else f'{url}/'
		_, _, user_host_port, sub = self._url.split('/', 3)
		self._sub = f'./{sub}'
		try:
			user, host_port = user_host_port.split('@', 1)
		except ValueError:
			user, host_port = '', user_host_port
		try:
			host, port = host_port.split(':', 1)
		except ValueError:
			host, port = host_port, 22
		self._retries = retries
		self._delay = delay
		try:
			self._ssh = SSHClient()
			self._ssh.set_missing_host_key_policy(AutoAddPolicy())
			self._ssh.connect(hostname=host, port=port, username=user, password=pw, timeout=timeout)
			self._sftp = self._ssh.open_sftp()
		except Exception as ex:
			Log.error(message=f'Unable to connect to {hostname}:{port} as {username}', exception=ex)

	def ls(self, match=None):
		'''List remote directory'''
		for attempt in range(1, self._retries+1):
			try:
				dir = self._sftp.listdir(self._sub)
			except:
				if attempt < self._retries:
					Log.debug(f'Attempt {attempt} to retrieve file list from {self._sub} failed, retrying in {self._delay} seconds')
					sleep(self._delay)
				else:
					Log.error(f'Unable to retrieve file list from {self._url}')
					return
		for item in dir:
			if match:
				if re_match(match, item):
					yield item
			else:
				yield item

	def download(self, remote_path, local_dir_path):
		'''Download file'''
		local_path = local_dir_path / remote_path.split('/')[-1]
		Log.debug(f'Downloading {remote_path} to {local_path}')
		for attempt in range(1, self._retries + 1):
			try:
				self._sftp.get(remote_path, f'{local_path}')
				Log.debug(f'Received file {local_path.name}')
				return local_path
			except:
				if attempt < self._retries:
					Log.debug(f'Attempt {attempt} of {self._retries} to retrieve {remote_path} failed, retrying in {self._delay} seconds')
					sleep(self._delay)
				else:
					Log.error(f'Unable to download {remote_path}')
					return

	def __del__(self):
		'''Close SFTP connection'''
		try:
			self._sftp.close()
			self._ssh.close()
		except:
			Log.error('Unable to close SFTP connection')
