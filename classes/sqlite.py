#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlite3 import connect
from time import time

class SQLiteDB:
	'''SQLite database for tracking file downloads and copy status'''

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
		self.conn.execute(
			'INSERT OR REPLACE INTO files (file_path, download_date, forward_date) VALUES (?, ?, ?)',
			(str(file_path), int(time()), 0)
		)
		self.conn.commit()

	def mark_forward(self, file_path):
		'''Mark file as copied'''
		self.conn.execute('UPDATE files SET forward_date = ? WHERE file_path = ?', (int(time()), str(file_path)))
		self.conn.commit()

	def get_uncopied(self):
		'''Get list of files not yet copied'''
		cursor = self.conn.execute('SELECT file_path FROM files WHERE copied = 0')
		return [row[0] for row in cursor.fetchall()]

	def close(self):
		'''Close database connection'''
		self.conn.close()