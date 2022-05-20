#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.1_2022-05-20'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Build zminow.exe using PyInstaller'

import PyInstaller.__main__
from pathlib import Path
from argparse import ArgumentParser

if __name__ == '__main__':	# start here if called as application
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('filepath', nargs=1, type=Path,
		help='Path to trigger file', metavar='FILEPATH'
	)
	args = argparser.parse_args()
	filepath = args.filepath[0].as_posix()
	zmidir = Path(__file__).resolve().parent
	script_orig = zmidir / 'zminow.py'
	script_copy = zmidir / 'zminow_tmp.py'
	icon = zmidir / 'zminow_96.ico'
	exe_name = 'zminow.exe'
	with open(script_orig, 'rt', encoding='utf8') as readf:
		with open(script_copy, 'wt', encoding='utf8') as writef:
			for line in readf:
				if line == '\tPATH_TO_TRIGGERFILE\n':
					writef.write(f"\tPATH_TO_TRIGGERFILE = Path(\'{filepath}\')\n")
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
