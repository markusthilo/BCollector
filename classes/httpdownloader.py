#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from urllib.request import urlopen, urlretrieve
from time import sleep
from html.parser import HTMLParser
from urllib.parse import quote, unquote
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
	
	def open_connection(self):
		'''Dummy method'''
		return True

	def handle_starttag(self, tag, attrs):
		'''Customize urllib.request'''
		if tag == 'a':
			for attr, value in attrs:
				if attr == 'href' and value and not value.startswith('?') and value != '/' and self.REGEX_IN_HREF.match(value):
					self._hrefs.append(value)

	def _url(self, path):
		'''Return URL'''
		return self._root + quote(f'{path}'.replace('\\', '/'))

	def iterdir(self, path):
		'''Iterate over remote directory'''
		url = self._url(path)
		self._hrefs = list()
		Log.debug(f'Fetching HTML data from {url}')
		for attempt in range(1, self._retries+1):
			try:
				with urlopen(url) as response:
					html = response.read().decode('utf-8')
			except:
				if attempt < self._retries:
					Log.debug(f'Attempt {attempt} to retrieve file list from {url} failed, retrying in {self._delay} seconds')
					sleep(self._delay)
				else:
					raise OSError(f'Unable to retrieve file list from {url}.')
					return list(), list()
		self.feed(html)
		dirs = list()
		files = list()
		for href in self._hrefs:
			rel = unquote(href)
			if href.endswith('/'):
				dirs.append(path / rel.lstrip('/'))
			else:
				files.append(path / rel)
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
				regex = re_compile(name)
				for path in self.files:
					if regex.match(path.name):
						yield path
			else:
				for path in self.files:
					yield path

	def download(self, remote_file_path, local_dir_path):
		'''Download file'''
		url = self._url(remote_file_path)
		Log.debug(f'Downloading {url} to {local_dir_path}')
		local_file_path = local_dir_path / remote_file_path
		Log.debug(f'{local_file_path=}')
		for attempt in range(1, self._retries+1):
			try:
				urlretrieve(url, local_file_path)
			except:
				if attempt < self._retries:
					Log.debug(f'Attempt {attempt} to retrieve {url} failed, retrying in {self._delay} seconds')
					sleep(self._delay)
				else:
					Log.error(f'Unable to download {url}')
			else:
				Log.debug(f'Received file {local_file_path}')
				return local_file_path

	def close_connection(self):
		'''Dummy method'''
		return True