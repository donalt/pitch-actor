# -*- coding: utf-8 -*-
from tkinter import filedialog
from tkinter import *
from PIL import Image, ImageTk

import numpy as np
import audio # Play / record audio
import synth # Synthesise voicelines
import dialog # Load and handle dialogue files.
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

THRESHOLD = 0.1 # Threshold for voice on/off.
P_COLOR = '#d62d20' # Color for pitch curve.

class PitchGUI:
	def __init__(self):
		self.synth = synth.Synth()
		self.audio = audio.Audio(self, self.synth)
		
		self.root = Tk()
		self.root.wm_title('PitchActor 0.0.1')

		window = Frame(self.root)
		window.pack(expand=1)

		#### toplevel menu ##################################################
		menubar = Menu(window)

		filemenu = Menu(menubar, tearoff=0)
		filemenu.add_command(label='Open wav...', command=self.open_wav_file)
		
		menubar.add_cascade(label='File', menu=filemenu)
		self.root.config(menu=menubar)


		#### control panel ##################################################
		controls = Frame(window)
		controls.pack()

		w = h = 50
		img1 = ImageTk.PhotoImage(file='../img/icon/stop.png')
		img2 = ImageTk.PhotoImage(file='../img/icon/play.png')
		img3 = ImageTk.PhotoImage(file='../img/icon/previous.png')
		img4 = ImageTk.PhotoImage(file='../img/icon/rec.png')
		img5 = ImageTk.PhotoImage(file='../img/oldicon/menu.png')
		img6 = ImageTk.PhotoImage(file='../img/icon/music.png')
		img7 = ImageTk.PhotoImage(file='../img/icon/rec2.png')
		self.stop_btn = Button(controls, image=img1, bd=0, height=h, width=w, text='Stop', command=self.stop_button)
		self.play_btn = Button(controls, image=img2, bd=0, height=h, width=w, text='Play', command=self.play_button)
		self.rewind_btn = Button(controls, image=img3, bd=0, height=h, width=w, text='Rewind', command=self.rewind_button)
		self.record_btn = Button(controls, image=img4, bd=0, height=h, width=w, text='Record', command=self.record_button)
		self.save_btn = Button(controls, image=img5, bd=0, height=h, width=w, text='Save', command=self.save_wav_file)
		self.listen_btn = Button(controls, image=img6, bd=0, height=h, width=w, text='Listen', command=self.listen_voice)
		self.stop_btn.img = img1
		self.play_btn.img = img2
		self.rewind_btn.img = img3
		self.record_btn.img  = img4
		self.record_btn.img2 = img7
		self.save_btn.img = img5
		self.listen_btn.img = img6
		self.listen_btn.pack(side=LEFT)
		self.play_btn.pack(side=LEFT)
		self.stop_btn.pack(side=LEFT)
		self.rewind_btn.pack(side=LEFT)
		self.record_btn.pack(side=LEFT, padx=(30,0))
		self.save_btn.pack(side=LEFT)


		#### pitch & volume graph ##################################################
		graph_frame = Frame(window)
		graph_frame.pack()
		yaxis_graph = Frame(graph_frame)
		self.graph = Canvas(yaxis_graph, width=GRAPH_W+1, height=GRAPH_H, bg='white', highlightthickness=0)
		#self.graph.bind('<Button-1>', self.click_playback_cursor)
		self.graph.bind('<Button-1>', self.mouse1_on_graph)
		self.graph.bind('<B1-Motion>', self.mouse1_on_graph)
		self.graph.bind('<Button-3>', self.mouse3_on_graph)
		self.graph.bind('<B3-Motion>', self.mouse3_on_graph)
		self.graph.bind('<Motion>', self.mouse_on_graph)

		# Vertical line used with audio playback.
		self.cursor_line = self.graph.create_line(0,0,0,0, fill='red')
		self.cursor_start_line  = self.graph.create_line(0,0,0,0)
		# Horizontal threshold line.
		self.threshold_line = self.graph.create_line(0, 0, GRAPH_W, 0,
		                                            fill='#005b96', dash='-', width=2)
		self.max_y = GRAPH_H
		self.set_threshold(THRESHOLD)
		# Border (xaxis canvas is used for lower line)
		self.graph.create_line(0, 0, 0, GRAPH_H)             # left y
		self.graph.create_line(GRAPH_W, 0, GRAPH_W, GRAPH_H) # right y
		self.graph.create_line(0, 0, GRAPH_W, 0)             # top y

		self.yaxis = Canvas(yaxis_graph, width=Y_WIDTH, height=GRAPH_H+Y_TOP, highlightthickness=0)
		self.xaxis = Canvas(graph_frame, width=Y_WIDTH+GRAPH_W+X_RIGHT, height=X_HEIGHT, highlightthickness=0)
		self.xaxis.create_line(Y_WIDTH,0, GRAPH_W+Y_WIDTH, 0) # low y
		self.yaxis.pack(side=LEFT)
		self.graph.pack(side=LEFT, padx=(0, X_RIGHT), pady=(Y_TOP, 0))
		yaxis_graph.pack()
		self.xaxis.pack()
		self.yaxis.bind('<Button-1>', self.mouse1_yaxis)

		#### dubbing move controls ##################################################
		dubbing = Frame(window)
		dubbing.pack()
		dubbtns = Frame(dubbing)
		dubbtns.pack()

		dialog_info = Label(dubbtns)
		self.dubbed = BooleanVar()
		self.dubbed.set(False)
		self.dubbed_btn = Checkbutton(dubbtns, text='Undubbed', variable=self.dubbed, indicatoron=0)
		prev_ln_btn = Button(dubbtns, text='Prev', command=self.prev_line)
		next_ln_btn = Button(dubbtns, text='Next', command=self.next_line)
		prev_char_btn = Button(dubbtns, text='PrevChar', command=self.prev_charline)
		next_char_btn = Button(dubbtns, text='NextChar', command=self.next_charline)
		self.line_entry = Entry(dubbtns, width=3, validate='key', vcmd=(dubbtns.register(self.valid_line_entry),'%d','%s','%S'))

		dialog_info.pack(side=LEFT, ipady=10, ipadx=20)
		self.dubbed_btn.pack(side=LEFT, ipady=10, ipadx=20)
		prev_ln_btn.pack(side=LEFT, ipady=10, ipadx=20)
		next_ln_btn.pack(side=LEFT, ipady=10, ipadx=20)
		prev_char_btn.pack(side=LEFT, ipady=10, ipadx=20)
		next_char_btn.pack(side=LEFT, ipady=10, ipadx=20)
		self.line_entry.pack(side=LEFT)

		#### dubbing dialogue text ##################################################
		lines = Frame(dubbing)
		lines.pack()
		# prev line, current line, next line
		p_line = Text(lines, width=80, height=3, wrap=WORD, cursor='arrow', state=DISABLED, fg='#252525', bg='#ddd')
		c_line = Text(lines, width=80, height=3, wrap=WORD, cursor='arrow', state=DISABLED)
		n_line = Text(lines, width=80, height=3, wrap=WORD, cursor='arrow', state=DISABLED, fg='#252525', bg='#ddd')
		p_line.pack()
		c_line.pack()
		n_line.pack()
		self.dialog = dialog.Dialog((p_line, c_line, n_line), dialog_info)
		

		### keyboard controls ######################################################
		# Player
		self.root.bind('<space>', self.space_key)
		self.root.bind('m', self.listen_voice)
		self.root.bind('r', self.record_button)
		self.root.bind(',', self.rewind_button)

		# Dubbing
		self.root.bind('d', self.toggle_dub_btn)
		self.root.bind('<Left>', self.prev_line)
		self.root.bind('<Right>', self.next_line)
		self.root.bind('<Up>', self.prev_charline)
		self.root.bind('<Down>', self.next_charline)

		self.audio.load_wav('../sound/test.wav') # TESTING
		self.synth.load_voice('../sound/sine220.wav', 110)
		#self.synth.load_voice('../sound/iii94.wav', 94)
		self.load_dialog('../dialog/test.txt')
		self.dirty = True
		window.mainloop()

	def draw_curve(self, x, y, tag, scale_fun, color='#000'):
		if x.size != y.size:
			raise ValueError('x and y must have same dimensions')
		# Scale to inverted y coords.
		y = scale_fun(y)
		y_lim = GRAPH_H
		curve = np.empty(y.size - 1, dtype=int)
		for i in range(curve.size):
			if y[i] > y_lim or y[i+1] > y_lim:
				curve[i] = self.graph.create_line(x[i], -2, x[i+1], -2, width=2, tags=tag, fill=color)
			else:
				curve[i] = self.graph.create_line(x[i], y[i], x[i+1], y[i+1], width=2, tags=tag, fill=color)
		return curve

	def gate_volume(self, index=-1):
		r = range(self.vol.size) if index==-1 else [index]
		for i in r:
			if self.vol[i] < self.threshold:
				c = '#f77'
				w = 1
			else:
				c = P_COLOR
				w = 3
			if i > 0:
				self.graph.itemconfig(self.p_lines[i-1], fill=c, width=w)
			if i < self.p_lines.size:
				self.graph.itemconfig(self.p_lines[i], fill=c, width=w)

	def alter_point(self, x, y, tag):
		self.dirty = True
		x = max(0, min(x, GRAPH_W))
		y = max(0, min(y, GRAPH_H))
		frame = int((x/GRAPH_W) * (self.max_x - 1) + 0.5)

		if tag == 'p':
			lines = self.p_lines
			values = self.pitch
			if values[frame] < 0:
				return
			self.pitch[frame] = self.scale_y2pitch(y)
		else:
			lines = self.v_lines
			values = self.vol
			# Transform y, cap it, and transform it back.
			vol_y = min(self.scale_y2vol(y), 0.999)
			y = self.scale_vol2y(vol_y)
			self.vol[frame] = vol_y
			self.gate_volume(frame)

		if frame > 0 and values[frame-1] >= 0: # Left line
			c = self.graph.coords(lines[frame - 1])
			c[3] = y
			self.graph.coords(lines[frame - 1], c)
		if frame < len(lines) and values[frame+1] >= 0: # Right line
			c = self.graph.coords(lines[frame])
			c[1] = y
			self.graph.coords(lines[frame], c)

	def draw_graph(self, pitch, vol):
		self.dirty = True
		self.pitch = pitch
		self.vol = vol
		self.max_x = pitch.size
		self.draw_pitch(pitch)
		self.draw_volume(vol)
		self.gate_volume()
		self.set_threshold(self.threshold)
		self.draw_axes()

	def draw_pitch(self, pitch):
		self.max_y = np.max(pitch) + PITCH_Y_PAD
		self.graph.delete('p')
		x = np.linspace(0, GRAPH_W, pitch.size)
		self.p_lines = self.draw_curve(x, pitch, 'p', self.scale_pitch2y, color=P_COLOR)

	def draw_volume(self, vol):
		self.graph.delete('v')
		x = np.linspace(0, GRAPH_W, vol.size)
		self.v_lines = self.draw_curve(x, vol, 'v', self.scale_vol2y)

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
		self.threshold = max(0, min(value, 1))
		value = self.scale_vol2y(self.threshold)
		self.graph.coords(self.threshold_line, [0, value, GRAPH_W, value])

	def scale_pitch2y(self, pitch):
		return GRAPH_H - pitch * (GRAPH_H / self.max_y)
	def scale_y2pitch(self, y):
		return (GRAPH_H - y) * (self.max_y/GRAPH_H)

	def scale_vol2y(self, vol):
		return GRAPH_H - vol * (GRAPH_H/2)
	def scale_y2vol(self, y):
		return (GRAPH_H - y) * (2/GRAPH_H)

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

	def load_dialog(self, path):
		self.dialog.load(path)

	###########    Buttons    ############
	def rewind_button(self, e=None):
		if not self.audio.recording():
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

	def record_button(self, e=None):
		if self.audio.recording():
			self.audio.stop_recording()
			self.record_btn.config(image=self.record_btn.img)
			self.listen_btn.config(state=NORMAL)
			self.play_btn.config(state=NORMAL)
			self.rewind_btn.config(state=NORMAL)
			self.rewind_button()
		else:
			self.audio.start_recording()
			self.record_btn.config(image=self.record_btn.img2)
			self.listen_btn.config(state=DISABLED)
			self.play_btn.config(state=DISABLED)
			self.rewind_btn.config(state=DISABLED)

	def listen_voice(self, e=None):
		if not self.audio.recording():
			self.record_btn.config(state=DISABLED)
			vol = np.copy(self.vol)
			vol[vol < self.threshold] = 0
			self.audio.play_voice(self.pitch, vol, self.dirty)
			self.root.after(0, self.play_callback)
			self.dirty = False

	def prev_line(self, e=None):
		self.dialog.prev()

	def next_line(self, e=None):
		self.dialog.next()

	def prev_charline(self, e=None):
		pass

	def next_charline(self, e=None):
		pass

	def valid_line_entry(self, inserting, oldstr, new):
		return True # TODO: PLACEHOLDER FOR MANIPULATING PITCH SHIFT
		if inserting != '1': # Don't validate deletion.
			return True
		# len <= 3 and no starting with 0.
		if (len(oldstr) + len(new)) > 3 or (oldstr=='' and new[0]=='0'):
			return False
		return True

	########### Keyboard Controls #############
	def toggle_dub_btn(self, e=None):
		self.dubbed_btn.toggle()

	def space_key(self, e=None):
		if self.audio.playing():
			self.stop_button()
		else:
			self.play_button()

	########### Mouse Events ############
	# Move cursor and stop audio if playing.
	def click_playback_cursor(self, event):
		if self.audio.loaded():
			self.audio.stop()
			self.audio.set_start(event.x / GRAPH_W)
			self.move_cursor(self.cursor_start_line, event.x)

	def mouse_on_graph(self, event):
		print(f'freq:{self.scale_y2pitch(event.y)}, vol:{self.scale_y2vol(event.y)}')

	def mouse1_on_graph(self, event):
		self.alter_point(event.x, event.y, 'p')

	def mouse3_on_graph(self, event):
		self.alter_point(event.x, event.y, 'v')

	def mouse1_yaxis(self, event):
		self.set_threshold(self.scale_y2vol(event.y - Y_TOP))
		self.gate_volume()