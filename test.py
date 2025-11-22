#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from classes.logger import Logger as Log
from classes.httpdownloader import HTTPDownloader
from classes.sftpdownloader import SFTPDownloader

Log()#.add_file(Path('test.log'))

#http = HTTPDownloader('http://localhost:8080/')
#print(http.ls())
#print()
sftp = SFTPDownloader('localhost', 'user', 'dummy', retries=1, delay=1)
print(sftp.ls())
print(sftp.download('test.bin', Path('./')))

Log.error('TEST ERROR')