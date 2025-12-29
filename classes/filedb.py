#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlite3 import connect
from pathlib import Path
from time import time

class FileDB:
	'''SQLite database for tracking file downloads and forward status'''

	def __init__(self, path):
		'''Initialize database connection and create table'''
		self._path = path
		self.open()
		self._conn.execute('''
			CREATE TABLE IF NOT EXISTS files (
				file_path TEXT UNIQUE NOT NULL,
				download_date INTEGER DEFAULT 0,
				forward_date INTEGER DEFAULT 0,
				delete_date INTEGER DEFAULT 0
			)
		''')
		self.close()

	def open(self):
		'''Open database connection'''
		self._conn = connect(self._path)

	def close(self):
		'''Close database connection'''
		self._conn.commit()
		self._conn.close()

	def add_download(self, file_path):
		'''Add file with current timestamp'''
		self._conn.execute(
			'INSERT OR REPLACE INTO files (file_path, download_date, forward_date, delete_date) VALUES (?, ?, 0, 0)',
			(str(file_path), int(time()))
		)

	def get_all(self):
		'''Get list of all files'''
		for row in self._conn.execute('SELECT file_path FROM files').fetchall():
			yield Path(row[0])

	def get_not_forwarded(self):
		'''Get list of files not yet forwarded'''
		for row in self._conn.execute('SELECT file_path FROM files WHERE forward_date = 0').fetchall():
			yield Path(row[0])

	def mark_forward(self, file_path):
		'''Mark file as copied'''
		self._conn.execute('UPDATE files SET forward_date = ? WHERE file_path = ?', (int(time()), str(file_path)))

	def get_forward_date(self, file_path):
		'''Check if file was forwarded'''
		return self._conn.execute('SELECT forward_date FROM files WHERE file_path = ?', (str(file_path),)).fetchone()[0]

	def mark_delete(self, file_path):	
		'''Mark file as deleted'''
		self._conn.execute('UPDATE files SET delete_date = ? WHERE file_path = ?', (int(time()), str(file_path)))

	def get_delete_date(self, file_path):
		'''Check if file was deleted'''
		return self._conn.execute('SELECT delete_date FROM files WHERE file_path = ?', (str(file_path),)).fetchone()[0]

	def get_older_than(self, timestamp):
		'''Get list of files older than given timestamp'''
		for row in self._conn.execute('SELECT file_path FROM files WHERE download_date < ?', (timestamp,)).fetchall():
			yield Path(row[0])

	def delete(self, arg):
		'''Delete file(s) from database'''
		for file_path in (arg, ) if isinstance(arg, Path) else arg:
			self._conn.execute('DELETE FROM files WHERE file_path = ?', (str(file_path), ))
