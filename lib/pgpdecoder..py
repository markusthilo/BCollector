#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class PgpDecoder:
	'Use command line PGP/GPG to decode'

	def __init__(self, cmd, passphrase):
		'Create decoder by giving the command line'
		self.cmd = cmd
		self.passphrase = passphrase

	def decode(self, encrypted, destdir):
		'Decode pgp file and return generated file'
		outfile = destdir / encrypted.stem
		pcmd = (
				self.cmd,
				'--pinentry-mode=loopback',
				'--passphrase', self.passphrase,
				'--output', outfile,
				'--decrypt', encrypted
		)
		logging.debug(f'Now executing: {pcmd}')
		process = Popen(pcmd, stdout = PIPE, stderr = STDOUT)
		while process.poll() is None:
			while True:
				err = process.stdout.readline().decode().strip()
				if err:
					logging.info(err)
				else:
					break
		if process.returncode == 0:
			return outfile
		logging.error(f'Could not decrypt {encrypted} to {outfile}')
		raise RuntimeError('Decoder returned error')
