# -*- coding: utf-8 -*-
import numpy as np
from tkinter import *
import audio
import pyaudio
import wave
import time # NOT NEEDED

class PitchGUI:
	### Constants
	CANVAS_W = 600
	CANVAS_H = 150

	PITCH_MAX_Y = 150
	PITCH_MIN_Y = 0

	def __init__(self):
		self.pyaudio = pyaudio.PyAudio()
		self.wf = None
		self.stream = None
		self.load_wav('../sound/test.wav')

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

		a = audio.Audio('../sound/test.wav', 2000)
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

		self.play_btn = Button(controls, text='Play', command=self.play_wav)
		self.play_btn.pack(side=LEFT, ipady=10, ipadx=20)

		self.record_btn = Button(controls, text='Record', command=self.record_wav)
		self.record_btn.pack(side=LEFT, ipady=10, ipadx=20)

		self.save_btn = Button(controls, text='Save', command=self.save_wav)
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

	def load_wav(self, file_name):
		if self.wf is not None:
			self.wf.close()
		self.wf = wave.open('../sound/test.wav', 'rb')

	def save_wav(self):
		pass

	def play_wav(self):
		# Stop playback if there is one, and rewind the file.
		if self.stream is not None:
			self.stream.stop_stream()
			self.stream.close()
		self.wf.rewind()

		self.stream = self.pyaudio.open(
			rate=self.wf.getframerate(),
			channels=1,
			format=self.pyaudio.get_format_from_width(self.wf.getsampwidth()),
			output=True,
			stream_callback=self.play_callback
		)

	def play_callback(self, in_data, frame_count, time_info, status):
		data = self.wf.readframes(frame_count)
		return (data, pyaudio.paContinue)

	def record_wav(self):
		pass

	def record_callback(self):
		pass

	def placeholder(self):
		pass