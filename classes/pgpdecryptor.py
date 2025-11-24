#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from gnupg import GPG
from classes.logger import Logger as Log

class PGPDecryptor:
	'''Decrypt PGP files, symmetric encryption with passphrase'''

	def __init__(self, passphrase):
		'''Create decryptor object to given passphrase'''
		self._passphrase = passphrase
		self._gpg = GPG()

	def decrypt(self, enc_file_path, dst_dir_path):
		'''Write decrypted file'''
		dst_file_path = dst_dir_path / enc_file_path.name.rstrip('.pgp').rstrip('.gpg')
		try:
			with open(enc_file_path, 'rb') as f:
				decrypted_data = self._gpg.decrypt_file(f, passphrase=self._passphrase)
				if decrypted_data.ok:
					dst_file_path.write_bytes(bytes(decrypted_data.data))
					return dst_file_path
				else:
					Log.error(f'Decryption failed, status: {decrypted_data.status}')
		except Exception as e:
			Log.error(f'Unable to open decrypted file {enc_file_path}')
