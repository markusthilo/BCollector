#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from subprocess import Popen, PIPE, STDOUT

class PgpDecoder:
	'Use command line PGP/GPG to decode'

	def __init__(self, cmd, passphrase):
		'Create decoder by giving the command line'
		self.cmd = cmd
		self.passphrase = passphrase

	def decode(self, encrypted_path, dir_path):
		'Decode pgp file and return generated file'
		decrypted_path = dir_path / encrypted_path.stem
		pcmd = (
				self.cmd,
				'--pinentry-mode=loopback',
				'--passphrase', self.passphrase,
				'--output', f'{decrypted_path}',
				'--decrypt', f'{encrypted_path}'
		)
		logging.debug(f'Now executing: {pcmd}')
		process = Popen(pcmd, stdout=PIPE, stderr=STDOUT)
		while process.poll() is None:
			while True:
				err = process.stdout.readline().decode().strip()
				if err:
					logging.error(err)
				else:
					break
		if process.returncode == 0:
			return decrypted_path
		logging.error(f'Could not decrypt {encrypted_path} to {decrypted_path}')
