#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.2_2022-07-15'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'GUI for file distribution'

from tkinter import Tk, PhotoImage, END
from tkinter.ttk import Frame, Button, LabelFrame
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
from shutil import copy2 as copy
from csv import DictReader

class CsvFile:
	'Filelist to proceed'

	FIELDNAMES = 'caseno,dstdep'

	def __init__(self, csvpath):
		'Open CSV file'
		self.fieldnames = [ fn.strip(' ') for fn in self.FIELDNAMES.split(',') ]
		self.filehandler = open(csvpath, 'r')
		self.reader = DictReader(self.filehandler)
		self.error = self.fieldnames != self.reader.fieldnames	# check for wrong csv file format

	def readall(self):
		'Read all tasks'
		for row in self.reader:
			yield tuple(row.values())

class Worker(CsvFile):
	'Move files given in the CSV file'

	SRCFILE = 'E:/unzugeordnet/ZMI_BE_&.zip'
	DSTPARENT = 'E:/'

	def __init__(self, csvpath):
		'Define the main window'
		super().__init__(csvpath)
		self.srcfile = self.SRCFILE.split('&')
		self.dstparentpath = Path(self.DSTPARENT)

	def moveall(self):
		'Move all files'
		for caseno, dstdep in self.readall():
			try:
				srcpath = Path(caseno.join(self.srcfile))
				dstpath = self.dstparentpath / dstdep
				copy(srcpath, dstpath)	# rename does not adapt permissions on windows
				srcpath.unlink()
				yield str(f'{caseno}, {dstdep}: moved {srcpath} to {dstpath}')
			except Exception as ex:
				yield(repr(ex))

class Main(Tk):
	'Main window'

	def __init__(self, icon_base64):
		'Define the main window'
		super().__init__()
		self.title('PostUp')
		self.resizable(0, 0)
		self.iconphoto(False, PhotoImage(data = icon_base64))
		self.frame_top = Frame(self)
		self.frame_top.pack(padx=10, pady=10, fill='x')
		Button(self.frame_top,
			text = 'Open CSV File',
			command = self.openfile
		).pack(fill='x')
		self.labelframe_infos = LabelFrame(self, text='Infos')
		self.labelframe_infos.pack(padx=10, pady=10, fill='x')
		self.infos = ScrolledText(
			self.labelframe_infos,
			padx = 10,
			pady = 10,
			width = 80,
			height = 10
		)
		self.infos.bind("<Key>", lambda e: "break")
		self.infos.insert(END, 'Select CSV File')
		self.infos.pack(padx=10, pady=10, side='left', fill='x')
		self.frame_bottom = Frame(self)
		self.frame_bottom.pack(padx=10, pady=10, side='right', fill='x')
		Button(self.frame_bottom,
			text="Quit", command=self.destroy).pack()

	def openfile(self):
		'Dialog to open CSV file and run task'
		worker = Worker(Path(askopenfilename(
			title = 'Open CSV File',
			filetypes = [("CSV files","*.csv")])
		))
		self.infos.config(state='normal')
		self.infos.delete(1.0, END)
		self.infos.configure(state='disabled')
		if worker.error:
			self.addinfo(
				f'Selected CSV file has wrong columns, this is rquired: {", ".join(worker.fieldnames)}'
			)
			showerror('Error', 'Wrong CSV file format')
		else:
			for msg in worker.moveall():
				self.addinfo(msg)

	def addinfo(self, msg):
		'Append info text'
		def append():
			self.infos.configure(state='normal')
			self.infos.insert(END, msg + '\n')
			self.infos.configure(state='disabled')
			self.infos.yview(END)
		self.infos.after(0, append)

if __name__ == '__main__':	# start here if called as application
	window = Main('''
iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAMAAADVRocKAAABZVBMVEUAN4YAOIYAOYcAOocAO4cA
PIcAPYgAPogCPogDPogMQIkTQokUQokVQokWQokZRIoeRYofRoohRosiR4sjR4snSYwqS4wvTY0y
T45MYJVNYJVPYpZQY5ZSZJdTZZdVZphaa5pcbJtreKFseaJteaJue6N1gKZ1gaZ2gaZ3gqZ3gqd4
g6d6hKh6hah8hqmIka+JkbCKk7GLk7GLlLGMlLKWnbiYn7mZoLmaobqborqdpLyfpbyfpb2hp76o
rsKrsMSsscWtssWtssaus8a1usu4vMy4vM2+wtC/w9HJzNjKzdjKzdnLztnQ093S1N7S1d7T1d/U
1t/V1+DX2eLY2uLd3+bg4ejg4ujh4unh4+ni4+nn6O3o6e7p6u7p6u/q6+/q6/Dr7PDs7fHt7vHt
7vLx8vXy8/Xz8/bz9Pb09Pf19ff19vj29vj29/j39/n6+vv6+/z7/Pz8/P39/f39/f7+/v7///8W
lkEhAAADwklEQVRo3u2a/1/SQBjHXQw8ECUSQwqzL4bISinNNCtBS92wRC3Kb6PS0gItle3vb0M2
7p7dTYbsl9rnl41t97zvdfd82150qS6rS1VrLkoH1AZjrmmwpgNiyDXFPIAH8AAewAP824ChfK6u
/NDVAHx6WZIk8XEcXI/IRsmVk1cBJD81zOxnQnCgoXKyfUDSnKeq5C2AY1neO9VufZGaEoecAG6V
se6jkoIAkeO6ZhTQpIh+B4BFYmiRBwBJOwZnzkiAzLUOCH8mhh4mKADkny7jTZAjALaRdW1I0rQf
AjSHMpugPtkZoP/U0qf9fmYFNMU5BKDePly9N7RJRjDAVwlIPHYGiO7IuMojNsvX1iZDI0KnAZEy
OTYDAAqllXa2B8uE/bIPAFZhK+3Ui9DdKmZfmQnQ4uBKXoReYoDNMOo8oDtfMea/GUcuABBKFQ91
+6WJMHIHgPiEIAgZnubC2zmg+R/OAHxGALrnbzMOgv3Q40IoOFGyjD4x6wmMEXpSNwHhN9/JiPlz
P2ApJRcT7GmMfG6mkAP9sqHdFL2iBW6vE/be+hNH9BnONUYGOENp7UW7z/zFrMmhzD5WHgdQhrEE
+7C/QIJq4yb4JsexzYRpAtMrCkBZhA6VDV7mRRILUI5YAVadD18CAPUYz0mjrQDUPAnggNh+rqpr
PhIwUpaBdL/KkW76+iPxxLvwqMIEnD0kAQE4O92vAAChgaUjwkTO5gPQeuiSxligAFAgMVUwirfW
nORtAMpNaDGYbThPig0AeXHX7hvWUgA8njUWtJpqEeCTKXa/GWaOEuDx5oJWx1oDUON4dcs4W2AC
1IooSRvacVtb6kK66UVEGM76H9EA0qRx9itqBbwQhKdVMKISNdL1sIhff4lEGqDAG68jyoQVoHdN
Y4BQi5lL1D251XTDbnqimEJ3zhunJZ4KQKlKM+UrBEBrFJcaUVZKMsqJgIIrxvkTPLD8JgBFmzVr
HADMiLzGKogC1imd4IE/mwONZTONM7woS0sUZw+0O3OUG5vR3MXbA6kNGwA1Uex1aXd6rIv3Ic5M
LCwAX2T3C9On4LIevE4BHC2O1d06wLdmtV8HWHpthQ2IH9iUkDSxP/XUUAeMw85nnA2g16hGdgkt
NDZxOXNRvfE4aNGLpuwANDkFFKhVINs5gEj3iI4Brv9sB7ACW6MVJiC4SgNshe0BTuIgXaU8PGlT
5ecdArT3GtjqFNN2rcTAjkzV+zCrZPKw1eHtGxWOLt77buoBPIAH8AAewAP8XwC3/3ri+p9nXNZf
w4PExebkqKEAAAAASUVORK5CYII=
	''')
	window.mainloop()
