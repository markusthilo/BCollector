#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from requests import get as get_http
from time import sleep
from bs4 import BeautifulSoup
from re import match as re_match
from urllib.request import urlretrieve

from classes.logger import Logger as Log

class HTTPDownloader:
	'Tools to fetch files via HTTP'

	def __init__(self, url, retries=10, delay=2):
		'''Initialize object'''
		self._url = url.rstrip('/')
		self._retries = retries
		self._delay = delay

	def ls(self, match=None):
		'''List remote directory / links in site'''
		for attempt in range(1, self._retries+1):
			try:
				soup = BeautifulSoup(get_http(self._url).text, 'html.parser')
				break
			except:
				if attempt < self._retries:
					Log.debug(f'Attempt {attempt} to retrieve file list from {self._url} failed, retrying in {self._delay} seconds')
					sleep(self._delay)
				else:
					Log.error(f'Unable to retrieve file list from {self._url}.')
					return
		for link in soup.find_all('a'):
			href = link.get('href')
			if match:
				if re_match(match, href):
					yield href
			else:
				yield href

	def download(self, filename, local_dir_path):
		'''Download file'''
		local_path = local_dir_path / filename
		url = self._url + filename
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

