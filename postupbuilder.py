#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.1_2022-05-25'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Build postup.exe using PyInstaller'

import PyInstaller.__main__ ### DEBUG ###
from pathlib import Path
from argparse import ArgumentParser

if __name__ == '__main__':	# start here if called as application
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-c', '--columns', type=str, metavar='STRING',
		default = 'caseno,dstdep',
		help='Comma seperated column names, default: "caseno,dstdep"'
	)
	argparser.add_argument('paths', nargs=2, type=Path, metavar='PATH',
		help='Source file and destination directory'
	)
	args = argparser.parse_args()
	fieldnames = args.columns
	srcfile = args.paths[0].as_posix()
	dstparent = args.paths[1].as_posix()
	zmidir = Path(__file__).resolve().parent
	script_orig = zmidir / 'postup.py'
	script_copy = zmidir / 'postup_tmp.py'
	icon = zmidir / 'postup_96.ico'
	exe_name = 'postup.exe'
	with open(script_orig, 'rt', encoding='utf8') as readf:
		with open(script_copy, 'wt', encoding='utf8') as writef:
			for line in readf:
				if line[:13] == '\tFIELDNAMES =':
					writef.write(f"\tFIELDNAMES = '{fieldnames}'\n")
				elif line[:10] == '\tSRCFILE =':
					writef.write(f"\tSRCFILE = '{srcfile}'\n")
				elif line[:12] == '\tDSTPARENT =':
					writef.write(f"\tDSTPARENT = '{dstparent}'\n")
				else:
					writef.write(line)
	PyInstaller.__main__.run([
		'--distpath', zmidir.as_posix(),
		'--icon', icon.as_posix(),
		'--onefile',
		'--name', exe_name,
		'--windowed',
		script_copy.as_posix()
	])
