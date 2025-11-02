#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from lxml.html import parse as parse_html
from urllib.request import urlretrieve
from time import sleep

class HttpDownloader:
	'Tools to fetch files via HTTP'

	def __init__(self, url, xpath, download_path, retries=10, delay=2):
		'Set source path'
		self._url = url
		self._xpath = xpath
		self._download_path = download_path
		self._retries = retries
		self._delay = delay

	def ls(self):
		'List source files'
		for at in range(1, self._retries+1):
			if logging.root.level == logging.DEBUG:
				print(f'DEBUG: Try to fetch file list from {self._url}')
			try:
				landing = parse_html(self._url)
			except Exception as e:
				msg = f'Attempt {at} of {self._retries} to retrieve file list from {self._url} failed:\n{e}'
				logging.warning(msg)
				if logging.root.level == logging.DEBUG:
					print(f'WARNING: {msg}')
				sleep(self._delay)
			else:
				msg = f'Received file list from {self._url} on attempt {at}'
				logging.info(msg)
				if logging.root.level == logging.DEBUG:
					print(f'INFO: {msg}')
				return (filename for filename in landing.xpath(self._xpath) if filename.endswith('.zip.pgp'))
		logging.error(f'Unable to retrieve file list from {self._url}.')

	def download(self, filename):
		'Download given file'
		source = self._url + filename
		dst_file_path = self._download_path / filename
		for at in range(1, self._retries+1):
			logging.debug(f'Attempt {at} downloading {source} to {self._download_path}')
			if logging.root.level == logging.DEBUG:
				print(f'DEBUG: Starting download of {source} to {dst_file_path}')
			try:
				urlretrieve(source, dst_file_path)
			except Exception as e:
				logging.error(f'Attempt {at} of {self._retries} to retrieve {source} failed:\n{e}')
				sleep(self._delay)
			else:
				logging.info(f'Received file {source} on attempt {at}')
				if logging.root.level == logging.DEBUG:
					print(f'DEBUG: Finished download of {source} to {dst_file_path}')
				return dst_file_path
		logging.error(f'Unable to download {source}')
