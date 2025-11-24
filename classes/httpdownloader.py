#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib.request import urlopen, urlretrieve
from bs4 import BeautifulSoup
from time import sleep
from re import match as re_match


from classes.logger import Logger as Log

class HTTPDownloader:
	'Tools to fetch files via HTTP'

	def __init__(self, url, match=None, retries=None, delay=None):
		'''Initialize object'''
		self._url = url.rstrip('/')
		self._match = match
		self._retries = retries if retries else 10
		self._delay = delay if delay else 2

	def ls(self):
		'''List remote directory / links in site'''
		for attempt in range(1, self._retries+1):
			try:
				with urlopen(self._url) as response:
					soup = BeautifulSoup(response.read(), 'html.parser')
			except:
				if attempt < self._retries:
					Log.debug(f'Attempt {attempt} to retrieve file list from {self._url} failed, retrying in {self._delay} seconds')
					sleep(self._delay)
				else:
					Log.error(f'Unable to retrieve file list from {self._url}.')
					return
			else:
				break
		for link in soup.find_all('a'):
			href = link.get('href')
			if self._match:
				if re_match(self._match, href):
					yield href
			else:
				yield href

	def download(self, filename, local_dir_path):
		'''Download file'''
		local_path = local_dir_path / filename
		url = f'{self._url}/{filename}'
		Log.debug(f'Downloading {url} to {local_path}')
		for attempt in range(1, self._retries+1):
			try:
				urlretrieve(url, local_path)
				return local_path
			except:
				if attempt < self._retries:
					Log.debug(f'Attempt {attempt} to download file {url} failed, retrying in {self._delay} seconds')
					sleep(self._delay)
				else:
					Log.error(f'Unable to download {url}')
					return

