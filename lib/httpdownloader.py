#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from lxml.html import parse as parse_html
from urllib.request import urlretrieve

class HttpDownloader:
	'Tools to fetch files via HTTP'

	def __init__(self, url, xpath, retries=10, delay=2):
		'Set source path'
		self.url = url
		self.xpath = xpath
		self.retries = retries
		self.delay = delay

	def ls(self):
		'List source files'
		for at in range(1, self.retries+1):
			try:
				landing = parse_html(self.url)
			except Exception as e:
				logging.error(f'Attempt {at} of {retries} to retrieve {self.url} failed:\n{e}')
				sleep(self.delay)
			else:
				logging.info(f'Received file list from {self.url} on attempt {at}')
				return (filename for filename in landing.xpath(self.xpath))
		logging.error(f'Unable to retrieve file list from {self.url}.')

	def download(self, filename, dir_path):
		'Download given file'
		source = self.url + filename
		dst_path = dir_path / filename
		for at in range(1, self.retries+1):
			logging.debug(f'Attempt {at} downloading {source} to {dir_path}')
			try:
				urlretrieve(source, dst_path)
			except Exception as e:
				logging.error(f'Attempt {at} of {retries} to retrieve {self.url} failed:\n{e}')
				sleep(self.delay)
			else:
				logging.info(f'Received file {self.url} on attempt {at}')
				return dst_path
		logging.error(f'Unable to download {source}.')
