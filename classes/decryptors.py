#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from gnupg import GPG
from py7zr import SevenZipFile
from classes.logger import Logger as Log

class PGPDecryptor:
	'''Decrypt PGP files, symmetric encryption with passphrase'''

	def __init__(self, passphrase):
		'''Create decryptor object to given passphrase'''
		self._passphrase = passphrase
		self._gpg = GPG()

	def suffix_match(self, path):
		'''Check if filename ends with .pgp or .gpg'''
		return path.suffix.lower() in ('.pgp', '.gpg')

	def decrypt(self, enc_file_path, dst_dir_path):
		'''Write decrypted file'''
		dst_file_path = dst_dir_path / enc_file_path.name[:-4]
		try:
			with open(enc_file_path, 'rb') as f:
				decrypted_data = self._gpg.decrypt_file(f, passphrase=self._passphrase)
				if decrypted_data.ok:
					dst_file_path.write_bytes(bytes(decrypted_data.data))
					return dst_file_path
				else:
					Log.error(f'Decryption failed, status: {decrypted_data.status}')
		except:
			Log.error(f'Unable to open decrypted PGP/GPG file {enc_file_path}')

class SevenZipDecryptor:
	'''Decrypt 7z files, symmetric encryption with passphrase'''

	def __init__(self, passphrase):
		'''Create decryptor object to given passphrase'''
		self._passphrase = passphrase

	def suffix_match(self, path):
		'''Check if filename ends with .7z'''
		return path.suffix.lower() == '.7z'

	def decrypt(self, enc_file_path, dst_dir_path):
		'''Write decrypted file'''
		dst_file_path = dst_dir_path / enc_file_path.name[:-3]

		
		try:
			with SevenZipFile(enc_file_path, mode='r', password=self._passphrase) as z:
				z.extractall(dst_file_path)
			return dst_file_path
		except:
			Log.error(f'Unable to open decrypted 7zip file {enc_file_path}')
