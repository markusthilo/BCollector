#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from lxml.html import parse as parse_html
from urllib.request import urlretrieve
from time import sleep

class HttpDownloader:
	'Tools to fetch files via HTTP'

	def __init__(self, url, xpath, target_dir_path, retries=10, delay=2):
		'Set source path'
		self.url = url
		self.xpath = xpath
		self.target_dir_path = target_dir_path
		self.retries = retries
		self.delay = delay

	def ls(self):
		'List source files'
		for at in range(1, self.retries+1):
			if logging.root.level == logging.DEBUG:
				print(f'DEBUG: Try to fetch file list from {self.url}')
			try:
				landing = parse_html(self.url)
			except Exception as e:
				msg = f'Attempt {at} of {self.retries} to retrieve file list from {self.url} failed:\n{e}'
				logging.warning(msg)
				if logging.root.level == logging.DEBUG:
					print(f'WARNING: {msg}')
				sleep(self.delay)
			else:
				msg = f'Received file list from {self.url} on attempt {at}'
				logging.info(msg)
				if logging.root.level == logging.DEBUG:
					print(f'INFO: {msg}')
				return (filename for filename in landing.xpath(self.xpath) if filename.endswith('.zip.pgp'))
		logging.error(f'Unable to retrieve file list from {self.url}.')

	def download(self, filename):
		'Download given file'
		source = self.url + filename
		dst_file_path = self.target_dir_path / filename
		for at in range(1, self.retries+1):
			logging.debug(f'Attempt {at} downloading {source} to {self.target_dir_path}')
			if logging.root.level == logging.DEBUG:
				print(f'DEBUG: Starting download of {source} to {dst_file_path}')
			try:
				urlretrieve(source, dst_file_path)
			except Exception as e:
				logging.error(f'Attempt {at} of {self.retries} to retrieve {source} failed:\n{e}')
				sleep(self.delay)
			else:
				logging.info(f'Received file {source} on attempt {at}')
				if logging.root.level == logging.DEBUG:
					print(f'DEBUG: Finished download of {source} to {dst_file_path}')
				return dst_file_path
		logging.error(f'Unable to download {source}')
