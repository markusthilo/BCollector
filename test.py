#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from classes.logger import Logger as Log
from classes.httpdownloader import HTTPDownloader
from classes.sftpdownloader import SFTPDownloader
from classes.pgpdecryptor import PGPDecryptor
from bcollector import BCollector

Log()#.add_file(Path('test.log'))

#http = HTTPDownloader('http://localhost:8080/')
#print(http.ls())
#print(http.ls('251014-Test'))
#print(http.download('251014-Test/test.bin', Path('./')))
#print()
#sftp = SFTPDownloader('localhost', 'user', 'dummy', retries=1, delay=1)
#print(sftp.ls())
#print(sftp.download('test.bin', Path('./')))
#pgp = PGPDecryptor('dummy')
#enc_path = Path('test.txt.gpg')
#dst_path = Path('../')
#pgp.decrypt(enc_path, dst_path)

collector = BCollector('http://localhost:8080/', Path('.'), Path('.'))

print(collector.ls())


