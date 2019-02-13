# -*- coding: utf-8 -*-
import numpy as np
from tkinter import filedialog
from tkinter import *
import audio
import time
import shutil # Copy files

# TODO: Put as much audio stuff as possible in separate file.
class PitchGUI:
	### Constants
	CANVAS_W = 600
	CANVAS_H = 200

	PITCH_MIN_Y = 0
	PITCH_Y_PAD = 10 # Extra headroom

	def __init__(self):
		self.audio = audio.Audio(self)

		self.root = Tk()
		self.root.wm_title('PitchActor 0.0.1')

		window = Frame(self.root)
		window.pack(padx=12, pady=(10,20))

		#### toplevel menu ##################################################
		menubar = Menu(window)

		filemenu = Menu(menubar, tearoff=0)
		filemenu.add_command(label='Open wav...', command=self.open_wav_file)
		
		menubar.add_cascade(label='File', menu=filemenu)
		self.root.config(menu=menubar)


		#### pitch & volume graph ##################################################
		self.graph = Canvas(self.root, width=self.CANVAS_W, height=self.CANVAS_H, bg='white')
		self.graph.bind('<Button-1>', self.click_playback_cursor)
		self.graph.pack(side=TOP)

		# Vertical line used with audio playback.
		self.cursor_line = self.graph.create_line(0,0,0,0, fill='red')
		self.cursor_start_line  = self.graph.create_line(0,0,0,0)

		# Horizontal threshold line.
		self.threshold_line = self.graph.create_line(0, 0, self.CANVAS_W, 0,
		                                            fill='#005b96', dash='-', width=2)
		self.set_threshold(self.audio.threshold)


		#### control panel ##################################################
		controls = Frame(window)
		controls.pack(fill=X)

		self.stop_btn = Button(controls, text='Stop', command=self.stop_button)
		self.stop_btn.pack(side=LEFT, ipady=10, ipadx=20)

		self.play_btn = Button(controls, text='Play', command=self.play_button)
		self.play_btn.pack(side=LEFT, ipady=10, ipadx=20)

		self.rewind_btn = Button(controls, text='Rewind', command=self.rewind_button)
		self.rewind_btn.pack(side=LEFT, ipady=10, ipadx=20)

		self.record_btn = Button(controls, text='Record', command=self.record_button)
		self.record_btn.pack(side=LEFT, ipady=10, ipadx=20)

		self.save_btn = Button(controls, text='Save', command=self.save_wav_file)
		self.save_btn.pack(side=LEFT, ipady=10, ipadx=20)

		self.audio.load_wav('../sound/test.wav') # TESTING
		window.mainloop()

	# Note, visible range is [2, CANVAS_H]
	def draw_curve(self, canvas, x, y, tag, color='#000'):
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
		
		# Scale to fit and invert.
		y = self.CANVAS_H - y * (self.CANVAS_H / self.max_pitch)
		max_y = self.CANVAS_H
		for i in range(y.size - 1):
			if y[i] < max_y and y[i+1] < max_y:
				canvas.create_line(x[i], y[i], x[i+1], y[i+1], width=2, tags=tag, fill=color)

	def draw_pitch(self, pitch):
		self.max_pitch = np.max(pitch) + self.PITCH_Y_PAD
		self.graph.delete('p')
		x = np.linspace(0, self.CANVAS_W, pitch.size)
		self.draw_curve(self.graph, x, pitch, 'p', color='red')

	def draw_volume(self, vol):
		self.graph.delete('v')
		x = np.linspace(0, self.CANVAS_W, vol.size)
		self.draw_curve(self.graph, x, vol * 150, 'v')

	def move_cursor(self, cursor, x):
		self.graph.coords(cursor, [x, 0, x, self.CANVAS_H])
		self.graph.update_idletasks()

	def play_callback(self):
		if self.audio.playing():
			x = self.CANVAS_W * self.audio.play_ratio()
			self.move_cursor(self.cursor_line, x)
			self.root.after(20, self.play_callback)
		else:
			self.record_btn.config(state=NORMAL)
			self.move_cursor(self.cursor_line, 0)

	def set_threshold(self, value):
		value = self.CANVAS_H - (value * 150)
		self.graph.coords(self.threshold_line, [0, value, self.CANVAS_W, value])

	def save_wav(self):
		pass

	########### Menu Options ############
	def open_wav_file(self):
		path = filedialog.askopenfilename(title='Select wav file', filetypes=(("wav file","*.wav"),))
		if len(path) > 0:
			self.audio.load_wav(path)

	def save_wav_file(self):
		path = filedialog.asksaveasfilename(title='Save audio clip as', filetypes=(("wav file","*.wav"),))
		if len(path) > 0:
			if path[-4:] != '.wav':
				path += '.wav'
			shutil.copy2(self.audio.TEMP_WAV, path)

	###########    Buttons   ############
	def rewind_button(self):
		self.audio.rewind()
		self.move_cursor(self.cursor_line, 0)
		self.move_cursor(self.cursor_start_line, 0)

	def play_button(self):
		self.record_btn.config(state=DISABLED)
		self.audio.play()
		self.root.after(0, self.play_callback)

	def stop_button(self):
		if self.audio.recording():
			self.record_button() # Stop btn functions like Record btn when recording.
		else:
			self.audio.stop()
			self.move_cursor(self.cursor_line, 0)

	# TODO: Disable other buttons while recording
	def record_button(self):
		if self.audio.recording():
			self.audio.stop_recording()
			self.play_btn.config(state=NORMAL)
			self.rewind_btn.config(state=NORMAL)
		else:
			self.audio.start_recording()
			self.play_btn.config(state=DISABLED)
			self.rewind_btn.config(state=DISABLED)

	########### Mouse Events ############
	# Move cursor and stop audio if playing.
	def click_playback_cursor(self, event):
		if self.audio.loaded():
			self.audio.stop()
			self.audio.set_start(event.x / self.CANVAS_W)
			self.move_cursor(self.cursor_start_line, event.x)
