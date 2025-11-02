#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from subprocess import Popen, PIPE, STDOUT

class PgpDecoder:
	'Use command line PGP/GPG to decode'

	def __init__(self, cmd, passphrase):
		'Create decoder by giving the command line'
		self._cmd = cmd
		self._passphrase = passphrase

	def decode(self, encrypted_path, decrypted_path):
		'Decode pgp file and return generated file'
		pcmd = (
				self._cmd,
				'--yes',
				'--pinentry-mode=loopback',
				'--passphrase', self._passphrase,
				'--output', f'{decrypted_path}',
				'--decrypt', f'{encrypted_path}'
		)
		process = Popen(pcmd,
			stdout = PIPE,
			stderr = STDOUT,
			universal_newlines = True,
			text = True,
			encoding = 'utf-8'
		)
		stdout, stderr = process.communicate()
		msg = stdout
		if stderr:
			msg += f'\n{stderr}'
		if process.returncode == 0:
			logging.debug(f'PGP: {msg}')
			return decrypted_path
		logging.error(f'Could not decrypt {encrypted_path} to {decrypted_path}: {msg}')
