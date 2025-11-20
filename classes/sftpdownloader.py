#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from paramiko import SSHClient, AutoAddPolicy
from time import sleep
from pathlib import Path

class SftpDownloader:
	'Tools to fetch files via SFTP'

	def __init__(self, hostname, username, password, port=22, timeout=30, retries=10, delay=2):
		'Set source path'
		self._retries = retries
		self._delay = delay
		#try:
		self._ssh = SSHClient()
		self._ssh.set_missing_host_key_policy(AutoAddPolicy())
		self._ssh.connect(hostname=hostname, port=port, username=username, password=password, timeout=timeout)
		self._sftp = self._ssh.open_sftp()
		#except Exception as ex:
		#	logging.error(f'Unable to connect to {hostname}:{port} as {username} - {type(ex).__name__}: {ex}')

	def ls(self, path='.'):
		'''List remote directory'''
		#try:
		return self._sftp.listdir(path)
		#except Exception as ex:
		#	logging.error(f'Unable to list {path} - {type(ex).__name__}: {ex}')

	def download(self, remote_path, local_dir_path):
		'''Download file'''
		local_path = local_dir_path / remote_path.split('/')[-1]
		logging.info(f'Retrieving {remote_path}')
		for attempt in range(1, self._retries + 1):
			try:
				self._sftp.get(remote_path, f'{local_path}')
				logging.info(f'Received file {remote_path}')
				return local_path
			except Exception as ex:
				logging.error(f'Attempt {attempt} of {self._retries} to retrieve {remote_path} failed - {type(ex).__name__}: {ex}')
				sleep(self._delay)
		logging.error(f'Unable to download {remote_path}')

	def __del__(self):
		'''Close SFTP connection'''
		try:
			self._sftp.close()
			self._ssh.close()
		except Exception as ex:
			logging.error(f'Unable to close SFTP connection - {type(ex).__name__}: {ex}')

# DEBUGGING

if __name__ == "__main__":
	downloader = SftpDownloader('localhost', 'user', 'dummy')
	print(downloader.ls())
	print(downloader.download('test.bin', Path('./')))
