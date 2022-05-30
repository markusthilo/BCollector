#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.1_2022-05-25'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Trigger ZMImport'

from tkinter import Tk, PhotoImage, LEFT, RIGHT
from tkinter.ttk import Button
from tkinter.messagebox import showinfo
from datetime import datetime
from os import remove, path
from pathlib import Path

class Main(Tk):
	'Main window'

	TRIGGERFILE = 'zminow.trigger'

	def __init__(self, icon_base64):
		'Define the main window'
		super().__init__()
		self.triggerpath = Path(self.TRIGGERFILE)
		self.title('SQLDump2Xlsx')
		self.resizable(0, 0)
		self.iconphoto(False, PhotoImage(data = icon_base64))
		Button(self,
			text="Import", command=self.importnow).pack(padx=10, pady=10, side=LEFT)
		Button(self,
			text="Quit", command=self.destroy).pack(padx=10, pady=10, side=RIGHT)

	def importnow(self):
		'Generate trigger file'
		with open(self.triggerpath, 'w') as f:
			f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		showinfo(title='ZMIport', message='Import is triggered')
		self.destroy()

if __name__ == '__main__':	# start here if called as application
	window = Main('''
iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAMAAADVRocKAAADAFBMVEUARQAAAAADBgEHCgUJDAgL
DgoNEAwPEQ4SFBETFRMUFhQWGBUXGBYYGRcZGxgaHBkbHBobHRsdHxweIB0fIR8hIyAiJCEjJSIl
JyUnKSYpKygrLSotLywwMi8yNDECPog1NjQAQYkAQYoAQos3OTYAQ4wARI04Ojg6PDqvHSo9PzwB
S44TR4s/QT4XSI0HTZCyITFCREEOT5O0JDhERkMTUZVHSUYXU5dLTUokU5O0LjobWJYnVZVPUU4e
Wpi3MkIgW5q6NUQkXZxTVVInYJ9XWVa6PUczYpxbXVq9QE82ZZ9dX1w4ZqEvaaJgYl8ya6UzbKa+
SVJjZWI9bqNlZ2TATFo/cKRoamdBcabET11Cc6jAU11qbWpEdapGdqvEVmBucG1IeK3GWGdydHFR
e6vFXml2eHXIYWxVf7B4enfLZG9YgrN7fXrIZ298f3xbhbbMa3Jih7PMbHmChIFliraEh4NojbnN
c32HiYZqj7uKjIlskb3SeIFyk7qNj4zQfYR0lbyPkY53mL/UgIeSlJHUgo55msGUlpOWmJXThpB8
ncSBnsDViZKCn8GZnJmEocOcnpvZjJaHpMaeoZ2JpsnYkpiho6CLqMvblZykpqOOq83ZmZ6SrMmo
qqeVr8zenaKqraqXsc6ZstDfoKqusK2btdKwsq/epq2euNW0trPiqrGku9LkrLO3uranvtbhsLW6
vLmqwdi8v7vls7isw9uuxd3otrzAw7+zx9nlur3DxsO2ytzovcDHyca5zd/JzMntwsW70OLDz+PN
z8y+0uXrx8jD1OHP0s7sydDG0+fF1uPM1eTwzM3S1dHvzdTV19TP2Oft0dbX2tbv1NnS3OrZ3NjV
3+3z2N3d39zb4urg4t/x3d/03+Le5e3i5eHg5/Dl5+T34+Xn6ebj6vPp6+j16Onl7PXr7ern7vf3
6+vo7/j67e7s8fTv8e7v9Pfx9PDy9vn69fP09/Tz+Pv1+fz3+fb/+fj3+/75+/j4/P/6/Pn//Pv5
/v/8/vv6//////86Xe6iAAAAAXRSTlMAQObYZgAABqtJREFUaN61ms9rGlsUx+c/cT0gInQVEdwp
PLIJhVLIohuzzMJScCVZiylduTI8SBcZitBJu4n5VaFhGkGCMSVgHJNKcBCJSd4MTJErh/vu/DCO
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
	''')
	window.mainloop()
