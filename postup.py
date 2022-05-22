#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.1_2022-05-20'
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
from csv import DictReader

class CsvFile:
	'Filelist to proceed'

	FIELDNAMES = ('caseno', 'dstdep')

	def __init__(self, csvpath):
		'Open CSV file'
		self.filehandler = open(csvpath, 'r')
		self.reader = DictReader(self.filehandler, fieldnames=self.FIELDNAMES)
		self.fieldnames = tuple(next(self.reader).values())	# read headline
		self.error = self.fieldnames != self.FIELDNAMES	# check for wrong csv file format

	def readall(self):
		'Read all tasks'
		for row in self.reader:
			yield tuple(row.values())

class Worker(CsvFile):
	'Move files given in the CSV file'

	SRCFILE = 'testfile&.txt'
	DSTPARENT = '~'

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
				dstpath = self.dstparentpath / srcpath.name
				srcpath.rename(dstpath)
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
				f'Selected CSV file has wrong columns: {", ".join(worker.fieldnames)}'
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
iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAMAAADVRocKAAAAw1BMVEUAAAAAAACCgoJCQkLCwsIi
IiKhoaFhYWHi4uISEhKSkpJSUlLR0dExMTGysrJycnLx8fEJCQmJiYlKSkrJyckqKiqpqalpaWnq
6uoZGRmZmZlaWlrZ2dk5OTm6urp6enr6+voFBQWGhoZFRUXFxcUlJSWlpaVmZmbl5eUVFRWVlZVV
VVXW1tY1NTW2trZ2dnb19fUNDQ2Ojo5NTU3Nzc0uLi6tra1ubm7u7u4eHh6dnZ1dXV3e3t4+Pj6+
vr5+fn7///8PfNfhAAAF4UlEQVRo3u2ay26rOhSGEdeJZZAFNtcBYgJCgMFighDk/Z/qLLPbBJLd
lCQ+o3M8bFV/rKv/ZVe7/MtL+y8COOf/CsCbU+QveBoIIcPUplwpwEM4JvradYw5sBjrCJ0VAuaW
rC5sndSiKAyjKETN1nME7dz+erdtbmTNuK0mE4nehooAnh93Ti3k7lYUVVUVRVYwGklscmUAlsj9
g6jq81zL876vosBgsakGwBHtJGC0qlz7WnlfWQWbTDUxKH0c664xWr12W3llGc7gq8miEGoALSSo
tANBegkprORyivI9oY/Gwp1mha0iXPc+0rQqyBLdVNmLzIOPpAmia5U2O6YdozAWLFYKiPNHH4Uq
AcMR0FuN6HyFAJ4cATnkkWMrBLTHPP3jo3VWBpid6Lj/5iOXKis0MlZ3Fmw+IqEaQBpnQdRr9z4y
ktVXAYCWuhqNdW9Cb2Wiw28C9uqBlymc+DZx7mzoo0Y8rbVnAM/7W6BpdhcEwyH8LQAvw7/+4dzd
B0Gf3wJ45Q/ZMdfHINQdes+CHw1Pg2MQ3EW1NqXHSmBYMcAjxyA8a0fviF/TvauEOlYB4NyDFc5t
99AthP4RgM/IN5cWU1iYxo722C2c+Zbb/Cng4feXdKHxMAxxPIC61odYF/cAaYL97T2M7/Skdude
m/r7+kWUgGJ312Gi1B6AQNYHwBaF7ehHE3wJLp8AQjro+mB+F9iM9aQwCuGsU+sjKe90QrpGe3RS
JmLTnGB+WAcaPrMAPtiFD8YIzChxV4CgDgLLSoYWpWixiU7iWM8enFQFTVFvk0k3LE9jgIaOJXJ1
A0kM2N0CQQ2KOg8SlozaTwt06pjBVJKwdQqfZxFdQanDpGFItW5Ffa+dWhvBEIlL0l/StIRZQ4Bn
to/vc+3s6qOgMSBYy6914BMwYfv6qtfOry0MiUv574VmElYbclh6DRBBJjE7PFPJSGfC2ALwAgD0
S+HQ8FyrmG1HyIGvegEApVBjfrYXcSoJwQsAKeQpP9/svDgpsjHKXzHgB/n1Qzf1IdDHme83A4r2
pXbtEcjV4GyY+yxoEvO184AycNJJQk8XBiF+DbDIlnEYvbds/2tUoHqpIfT0JQCibUvqgxiF4T6C
8ntgTDJm0CboS4Ay5XA6JEVzdVMfWePQUnbvtkBmJzKKH4Y17anqWpwt1PDRPbTL2twy+C65tgN/
AUCXvnHom0wS5A0O5MnXyT4c62OTLLEEoHdUBXJlqC0LWtm3cgjZocSd7UdvAy4pk32pycRtjMHW
3oTevPDFgMNmfQ9wMR1hwGG1U4f+uI9C36GUFqAM/i7iTwiv2BFCOLsU8cUeUK0obYWo2eC9CUCu
kzh79Ym6XRD6pg0906mdbnpbm8agZPatDMU3QJ9IJYeYw3641zkDMPV1JxZKn7Krixwc/jGSdTF/
GzDT6x0s9+01uR4UY/vldn9dB/TBrePtnhrpcE5cm8W1+/i2jdQMICGByr5G4Or1FHmqJpxWNLde
9H0E8FDdCGWK5taK2FfoucIHCix2WiAf5ufz7usATgGwq+I45Tycvc8AfHejELbuzkVaP04wmPjl
ZwAP+dcgeqa+B+QRszFe5g8tQAv6tiE0u4Mei4rBpu2HgMuchjtl3BwABgA+teDor6nZn/qRiCk2
Q4WAMs72h36UAMBXCAhbBq3iVgiRIBM2PWUAPredsa+0qHGJrdRF3Nd3zUheFrnDohIAXhpu7VRe
CdYrVgu4lMnVR70EuFQx4NLdAWzFgNn4Bsj5XgK42hjo32dmLsd7kIxUKSBd/+jtXI4LwZgJZ8Uf
AfjhATzE28hQfb2YykdZprefvR/wsJy/ToQZu3KuCiwpt+WbL0hetj5/DDzTrku/xW3bUnmXJB9l
QWw3WWZs90Od/suj7zldhKd40NeOOfV2lbTtLd/dVxK3Sp4aUzoNRO9c5iRJXSewOXw5bU00//pk
fTKLQh/bYIT8twF58Yf9pwf9m2nqlTMc8D6aw1fS+r3b9/8BKtc/NFcHINi4Q8kAAAAASUVORK5C
YII=
	''')
	window.mainloop()
