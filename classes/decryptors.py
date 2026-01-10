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
		Log.debug(f'Decrypting {enc_file_path} to {dst_file_path}')
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
		name = enc_file_path.name[:-3]
		try:
			zf = SevenZipFile(enc_file_path, mode='r', password=self._passphrase)
			ls = zf.list()
		except:
			Log.error(f'Unable to open file {enc_file_path}')
			zf.close()
			return
		dst_path = dst_dir_path if len(ls) == 1 and ls[0].is_file and ls[0].filename == name else dst_dir_path / name
		Log.debug(f'Decrypting/unpacking {enc_file_path} to {dst_path}')
		try:
			zf.extractall(dst_path)
		except:
			Log.error(f'Unable to extract file {enc_file_path}')
			dst_path = None
		zf.close()
		return dst_path
