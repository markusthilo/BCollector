#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib.request import urlopen, urlretrieve
from time import sleep
from re import compile as re_compile
from html.parser import HTMLParser
from classes.logger import Logger as Log

class HTTPDownloader(HTMLParser):
	'Tools to fetch files via HTTP'

	def __init__(self, url, retries=None, delay=None):
		'''Initialize object'''
		super().__init__()
		self._url = url.rstrip('/')
		self._match = match
		self._retries = retries if retries else 10
		self._delay = delay if delay else 2
		self._hrefs = list()
		self._regex = None

	def handle_starttag(self, tag, attrs):
		if tag == 'a':
			for attr, value in attrs:
				if attr == 'href' and ( not self._regex or self._regex.match(value) ):
					self._hrefs.append(value)

	def find(self, name=None):
		'''List remote directory / links in site'''
		self._regex = re_compile(name) if name else None
		for attempt in range(1, self._retries+1):
			try:
				with urlopen(self._url) as response:
					html = response.read().decode('utf-8')
			except:
				if attempt < self._retries:
					Log.debug(f'Attempt {attempt} to retrieve file list from {self._url} failed, retrying in {self._delay} seconds')
					sleep(self._delay)
				else:
					Log.error(f'Unable to retrieve file list from {self._url}.')
					return
			else:
				break
		self.feed(html)
		return self._hrefs

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
