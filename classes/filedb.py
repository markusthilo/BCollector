#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlite3 import connect
from pathlib import Path
from time import time

class FileDB:
	'''SQLite database for tracking file downloads and forward status'''

	def __init__(self, db_path):
		'''Initialize database connection and create table'''
		self._conn = connect(db_path)
		self._conn.execute('''
			CREATE TABLE IF NOT EXISTS files (
				file_path TEXT UNIQUE NOT NULL,
				download_date INTEGER DEFAULT 0,
				forward_date INTEGER DEFAULT 0
			)
		''')
		self._conn.commit()

	def add_download(self, file_path):
		'''Add file with current timestamp'''
		self._conn.execute(
			'INSERT OR REPLACE INTO files (file_path, download_date, forward_date) VALUES (?, ?, 0)',
			(str(file_path), int(time()))
		)
		self._conn.commit()

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
		self._conn.commit()

	def get_older_than(self, timestamp):
		'''Get list of files older than given timestamp'''
		for row in self._conn.execute('SELECT file_path FROM files WHERE download_date < ?', (timestamp,)).fetchall():
			yield Path(row[0])

	def delete(self, file_path):
		'''Delete file from database'''
		self._conn.execute('DELETE FROM files WHERE file_path = ?', (str(file_path), ))
		self._conn.commit()

	def close(self):
		'''Close database connection'''
		self._conn.close()
