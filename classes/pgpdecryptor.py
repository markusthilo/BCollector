#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pgpy import PGPMessage
from classes.logger import Logger as Log

class PGPDecryptor:
	'''Decrypt PGP files, symmetric encryption with passphrase'''

	def __init__(self, passphrase):
		'''Create decryptor object to given passphrase'''
		self._passphrase = passphrase

	def decrypt(self, enc_file_path, dst_dir_path):
		'''Write decrypted file'''
		dst_file_path = dst_dir_path / enc_file_path.name.rstrip('.pgp').rstrip('.gpg')
		try:
			dst_file_path.write_bytes(PGPMessage.from_file(enc_file_path).decrypt(self._passphrase).message)
			return dst_file_path
		except:
			Log.error(f'Unable to decrypt {enc_file_path}')
