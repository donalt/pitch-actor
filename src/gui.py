# -*- coding: utf-8 -*-
import numpy as np
from tkinter import *
from audio import Audio

class PitchGUI:
	### Constants
	CANVAS_W = 600
	CANVAS_H = 150

	PITCH_MAX_Y = 150
	PITCH_MIN_Y = 0

	def __init__(self):
		self.root = Tk()
		self.root.wm_title('PitchActor 0.0.1')

		window = Frame(self.root)
		window.pack(padx=12, pady=(10,20))

		#### toplevel menu ##################################################
		menubar = Menu(window)

		filemenu = Menu(menubar, tearoff=0)
		filemenu.add_command(label='Testing', command=self.placeholder)
		
		menubar.add_cascade(label='File', menu=filemenu)
		self.root.config(menu=menubar)


		#### pitch & volume graph ##################################################
		self.pitch_graph = Canvas(self.root, width=self.CANVAS_W, height=self.CANVAS_H, bg='white')
		self.pitch_graph.pack(side=TOP)

		a = Audio('../sound/test.wav', 5512)
		pitch, mag = a.pitch_mag()

		x = np.linspace(0, self.CANVAS_W, 200)
		y = 50*np.sin(2*np.pi*x)+75

		x = np.linspace(0, self.CANVAS_W, pitch.size)
		y = pitch
		self.draw_curve(self.pitch_graph, x, pitch)


		#### magnitude & threshold graph ##################################################
		self.mag_graph = Canvas(self.root, width=self.CANVAS_W, height=self.CANVAS_H, bg='white')
		self.mag_graph.pack(side=TOP)

		self.draw_curve(self.mag_graph, x, mag)
		self.threshold_line = self.mag_graph.create_line(0, 0, self.CANVAS_W, 0,
		                                                 fill='#005b96', dash='-', width=2)
		self.set_threshold(25)

		#### control panel ##################################################
		controls = Frame(window)
		controls.pack(fill=X)

		self.record_btn = Button(controls, text='Record', command=self.record)
		self.record_btn.pack(side=LEFT, ipady=10, ipadx=20)

		self.save_btn = Button(controls, text='Save', command=self.save_audio)
		self.save_btn.pack(side=LEFT, ipady=10, ipadx=20)

		window.mainloop()

	def draw_curve(self, canvas, x, y):
		if x.size != y.size:
			raise ValueError('x and y must have same dimensions')
		# Polygon gives error
		#xy = np.empty(x.size, dtype=tuple)
		#xy[0::2] = x
		#xy[1::2] = y
		#xy = np.vstack((x, y)).T
		#print(xy.shape)
		#canvas.create_polygon(xy)
		# Manually draw each line instead.
		y = self.PITCH_MAX_Y - y
		for i in range(y.size - 1):
			if np.all(np.isfinite(y[i:i+2])):
				canvas.create_line(x[i], y[i], x[i+1], y[i+1], width=2)

	def set_threshold(self, value):
		value = self.CANVAS_H - value
		self.mag_graph.coords(self.threshold_line, [0, value, self.CANVAS_W, value])

	def record(self):
		pass

	def save_audio(self):
		pass

	def placeholder(self):
		pass