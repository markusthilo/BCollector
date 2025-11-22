#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from requests import get as get_http
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from time import sleep
from classes.logger import Logger as Log

class HTTPDownloader:
	'Tools to fetch files via HTTP'

	def __init__(self, base_url, retries=10, delay=2):
		'Initialize object'
		self._base_url = base_url.rstrip('/')
		self._retries = retries
		self._delay = delay

	def ls(self, sub=''):
		'List source files'
		url = self._base_url+sub
		for attempt in range(1, self._retries+1):
			try:
				soup = BeautifulSoup(get_http(url).text, 'html.parser')
				break
			except:
				if attempt < self._retries:
					Log.debug(f'Attempt {attempt} to retrieve file list from {url} failed, retrying in {self._delay} seconds')
					sleep(self._delay)
				else:
					logging.error(f'Unable to retrieve file list from {url}.')
					return
		return [link.get('href') for link in soup.find_all('a')]

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
