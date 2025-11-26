#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from urllib.request import urlopen, urlretrieve
from time import sleep
from html.parser import HTMLParser
from re import compile as re_compile
from classes.logger import Logger as Log

class HTTPDownloader(HTMLParser):
	'Tools to fetch files via HTTP'

	REGEX_IN_HREF = re_compile(r'^(?!https?://|ftp://|ftps://|mailto:|tel:|javascript:).*')

	def __init__(self, url, retries=None, delay=None):
		'''Initialize object'''
		super().__init__()
		self._root = f'{url.rstrip("/")}/'
		self._retries = retries if retries else 10
		self._delay = delay if delay else 2
		self.dirs = list()
		self.files = list()

	def handle_starttag(self, tag, attrs):
		'''Customize urllib.request'''
		if tag == 'a':
			for attr, value in attrs:
				if attr == 'href' and self.REGEX_IN_HREF.match(value):
					self._hrefs.append(value)

	def iterdir(self, path):
		'''Iterate over remote directory'''
		for attempt in range(1, self._retries+1):
			self._hrefs = list()
			try:
				with urlopen(f'{self._root}{path}') as response:
					html = response.read().decode('utf-8')
			except:
				if path != Path(''):
					return list(), list()
				if attempt < self._retries:
					Log.debug(f'Attempt {attempt} to retrieve file list from {self._root}{path} failed, retrying in {self._delay} seconds')
					sleep(self._delay)
				else:
					raise OSError(f'Unable to retrieve file list from {self._root}{path}.')
		self.feed(html)
		dirs = list()
		files = list()
		for href in self._hrefs:
			if href.endswith('/'):
				dirs.append(path / href)
			else:
				files.append(path / href)
		self.dirs.extend(dirs)
		self.files.extend(files)
		for dir_path in dirs:
			dirs, files = self.iterdir(dir_path)
		return dirs, files

	def find(self, name=None):
		'''List remote files'''
		try:
			self.iterdir(Path(''))
		except Exception as ex:
			Log.error(exception=ex)
		else:
			if name:
				regex = re_compile(name) if name else None
				for path in self.files:
					if regex.match(path.name):
						yield path
			else:
				for path in self.files:
					yield path


		'''
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
		'''

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
