# -*- coding: utf-8 -*-
from tkinter import filedialog
from tkinter import *

import numpy as np
import audio
import shutil # Copy files

### Constants
GRAPH_W = 600
GRAPH_H = 200

X_HEIGHT = 17 # Height of x-axis.
Y_WIDTH = 30  # Width of y-axis.
Y_TOP = 7 # y-axis top pad, to show largest y-value.
X_RIGHT = 15 # x-axis right pad.

PITCH_Y_PAD = 10 # Extra headroom over pitch curve.
Y_SKIP = 10 # How many y pixels to move the lowest tick by.

class PitchGUI:
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
		yaxis_graph = Frame(self.root)
		self.graph = Canvas(yaxis_graph, width=GRAPH_W+1, height=GRAPH_H, bg='white', highlightthickness=0)
		#self.graph.bind('<Button-1>', self.click_playback_cursor)
		self.graph.bind('<Button-1>', self.mouse1_on_graph)
		self.graph.bind('<B1-Motion>', self.mouse1_on_graph)
		self.graph.bind('<Button-3>', self.mouse3_on_graph)
		self.graph.bind('<B3-Motion>', self.mouse3_on_graph)

		# Vertical line used with audio playback.
		self.cursor_line = self.graph.create_line(0,0,0,0, fill='red')
		self.cursor_start_line  = self.graph.create_line(0,0,0,0)
		# Horizontal threshold line.
		self.threshold_line = self.graph.create_line(0, 0, GRAPH_W, 0,
		                                            fill='#005b96', dash='-', width=2)
		self.set_threshold(self.audio.threshold)
		# Border (xaxis canvas is used for lower line)
		self.graph.create_line(0, 0, 0, GRAPH_H)             # left y
		self.graph.create_line(GRAPH_W, 0, GRAPH_W, GRAPH_H) # right y
		self.graph.create_line(0, 0, GRAPH_W, 0)             # top y

		self.yaxis = Canvas(yaxis_graph, width=Y_WIDTH, height=GRAPH_H+Y_TOP, highlightthickness=0)
		self.xaxis = Canvas(self.root, width=Y_WIDTH+GRAPH_W+X_RIGHT, height=X_HEIGHT, highlightthickness=0)
		self.xaxis.create_line(Y_WIDTH,0, GRAPH_W+Y_WIDTH, 0) # low y
		self.yaxis.pack(side=LEFT)
		self.graph.pack(side=LEFT, padx=(0, X_RIGHT), pady=(Y_TOP, 0))
		yaxis_graph.pack()
		self.xaxis.pack()
		

		#### control panel ##################################################
		controls = Frame(window)
		controls.pack(fill=X)

		self.stop_btn = Button(controls, text='Stop', command=self.stop_button)
		self.play_btn = Button(controls, text='Play', command=self.play_button)
		self.rewind_btn = Button(controls, text='Rewind', command=self.rewind_button)
		self.record_btn = Button(controls, text='Record', command=self.record_button)
		self.save_btn = Button(controls, text='Save', command=self.save_wav_file)

		self.stop_btn.pack(side=LEFT, ipady=10, ipadx=20)
		self.play_btn.pack(side=LEFT, ipady=10, ipadx=20)
		self.rewind_btn.pack(side=LEFT, ipady=10, ipadx=20)
		self.record_btn.pack(side=LEFT, ipady=10, ipadx=20)
		self.save_btn.pack(side=LEFT, ipady=10, ipadx=20)

		self.audio.load_wav('../sound/test.wav') # TESTING
		window.mainloop()

	def draw_curve(self, x, y, tag, color='#000'):
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
		y = GRAPH_H - y * (GRAPH_H / self.max_y)
		y_lim = GRAPH_H
		for i in range(y.size - 1):
			if y[i] <= y_lim and y[i+1] <= y_lim:
				self.graph.create_line(x[i], y[i], x[i+1], y[i+1], width=2, tags=tag, fill=color)

	def alter_curve(self, x, y, tag):
		tag = (tag,) # gettags() returns a tuple of tags
		x = max(0, min(x, GRAPH_W))
		y = max(0, min(y, GRAPH_H))
		frame = int((x/GRAPH_W) * (self.max_x))
		if frame == self.max_x:
			frame -= 1

		frame_x = (frame / (self.max_x - 1)) * GRAPH_W
		items = self.graph.find_overlapping(frame_x-1,-1, frame_x+1,GRAPH_H+1)
		
		for i in items:
			# Find pitch lines.
			if self.graph.gettags(i) == tag:
				c = self.graph.coords(i)
				# Update first or second point.
				if abs(c[0] - frame_x) < 0.05:
					c[1] = y
				else:
					c[3] = y
				self.graph.coords(i, c)

	def draw_graph(self, pitch, vol):
		self.max_x = pitch.size
		self.draw_pitch(pitch)
		self.draw_volume(vol)
		self.draw_axes()

	def draw_pitch(self, pitch):
		self.max_y = np.max(pitch) + PITCH_Y_PAD
		self.graph.delete('p')
		x = np.linspace(0, GRAPH_W, pitch.size)
		self.draw_curve(x, pitch, 'p', color='red')

	def draw_volume(self, vol):
		self.graph.delete('v')
		x = np.linspace(0, GRAPH_W, vol.size)
		self.draw_curve(x, vol * 150, 'v')

	def draw_axes(self):
		self.xaxis.delete('v')
		v = np.linspace(0, self.max_x, num=10, dtype=int)
		for i, x in enumerate(np.linspace(0, GRAPH_W, num=10, dtype=int)):
			self.xaxis.create_line(x+Y_WIDTH,0, x+Y_WIDTH,5, tags='t') # Ticks
			self.xaxis.create_text(x+Y_WIDTH,4, text=str(v[i]), anchor=N, tags='v') # Values
		
		self.yaxis.delete('v')
		v = np.linspace(self.max_y, Y_SKIP * (GRAPH_H / self.max_y), num=8, dtype=int)
		for i, y in enumerate(np.linspace(0, GRAPH_H-Y_SKIP, num=8, dtype=int)):
			self.yaxis.create_line(Y_WIDTH-5, y+Y_TOP, Y_WIDTH, y+Y_TOP, tags='t')
			self.yaxis.create_text(Y_WIDTH-8, y+Y_TOP, text=str(int(v[i])), anchor=E, tags='v')

	def move_cursor(self, cursor, x):
		self.graph.coords(cursor, [x, 0, x, GRAPH_H])
		self.graph.update_idletasks()

	def play_callback(self):
		if self.audio.playing():
			x = GRAPH_W * self.audio.play_ratio()
			self.move_cursor(self.cursor_line, x)
			self.root.after(20, self.play_callback)
		else:
			self.record_btn.config(state=NORMAL)
			self.move_cursor(self.cursor_line, -2)

	def set_threshold(self, value):
		value = GRAPH_H - (value * 150)
		self.graph.coords(self.threshold_line, [0, value, GRAPH_W, value])

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
		self.move_cursor(self.cursor_line, -2)
		self.move_cursor(self.cursor_start_line, -2)

	def play_button(self):
		self.record_btn.config(state=DISABLED)
		self.audio.play()
		self.root.after(0, self.play_callback)

	def stop_button(self):
		if self.audio.recording():
			self.record_button() # Stop btn functions like Record btn when recording.
		else:
			self.audio.stop()
			self.move_cursor(self.cursor_line, -2)

	# TODO: Disable other buttons while recording
	def record_button(self):
		if self.audio.recording():
			self.audio.stop_recording()
			self.play_btn.config(state=NORMAL)
			self.rewind_btn.config(state=NORMAL)
			self.rewind_button()
		else:
			self.audio.start_recording()
			self.play_btn.config(state=DISABLED)
			self.rewind_btn.config(state=DISABLED)

	########### Mouse Events ############
	# Move cursor and stop audio if playing.
	def click_playback_cursor(self, event):
		if self.audio.loaded():
			self.audio.stop()
			self.audio.set_start(event.x / GRAPH_W)
			self.move_cursor(self.cursor_start_line, event.x)

	def mouse1_on_graph(self, event):
		self.alter_curve(event.x, event.y, 'p')

	def mouse3_on_graph(self, event):
		self.alter_curve(event.x, event.y, 'v')