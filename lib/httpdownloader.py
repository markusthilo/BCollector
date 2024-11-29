#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class HttpDownloader:
	'Tools to fetch files via HTTP'

	def __init__(self, path, xpath):
		'Set source path'
		self.path = path
		self.xpath = xpath

	def basedir(self, retries=10, delay=2):
		'List source files as set'
		for at in range(1, retries+1):
			try:
				landing = parse_html(self.path)
				logging.debug(f'Received {self.path} on attempt {at}')
				return ( filename for filename in landing.xpath(self.xpath) )
			except OSError:
				logging.error(f'Attempt {at} of {retries} to retrieve {self.path} failed')
				sleep(delay)
		logging.error(f'Could not retrieve {self.path}')
		raise RuntimeError(f'Could not retrieve {self.path}')

	def download(self, filename, dstpath, retries=10, delay=2):
		'Download given file and generate sha256'
		sourcepath = self.path + filename
		filepath = dstpath / filename
		for at in range(1, retries+1):
			logging.debug(f'Attempt {at} downloading {sourcepath} to {dstpath}')
			with urlopen(sourcepath) as response:
				sourcefile = response.read()
			with open(filepath, 'wb') as filehandler:
				filelen = filehandler.write(sourcefile)
			if filelen == len(sourcefile):
				logging.debug(f'Building sha256 for {filename}')
				h = sha256()
				h.update(sourcefile)
				return sourcepath, filepath, h.hexdigest()
			logging.error(f'Source file has {len(sourcefile)} bytes but wrote {filelen} bytes')
		logging.error(f'Error while downloading {sourcepath}')
		raise RuntimeError(f'Error while downloading {sourcepath}')
