# -*- coding: utf-8 -*-
import numpy as np
from tkinter import filedialog
from tkinter import *
import audio
import pyaudio
import wave
import time

# TODO: Put as much audio stuff as possible in separate file.
class PitchGUI:
	### Constants
	CANVAS_W = 600
	CANVAS_H = 150

	PITCH_MAX_Y = 150
	PITCH_MIN_Y = 0

	RECORD_RATE = 11025
	TEMP_WAV = 'tmp.wav'

	def __init__(self):
		# Audio stuff
		self.pyaudio = pyaudio.PyAudio()
		self.wf = None
		self.stream = None
		self.start_ratio = 0
		self.recording = False

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
		self.pitch_graph = Canvas(self.root, width=self.CANVAS_W, height=self.CANVAS_H, bg='white')
		self.pitch_graph.bind('<Button-1>', self.click_playback_cursor)
		self.pitch_graph.pack(side=TOP)

		# Vertical line used with audio playback.
		self.cursor_line = self.pitch_graph.create_line(0,0,0,0, fill='red')
		self.cursor_start_line  = self.pitch_graph.create_line(0,0,0,0)


		#### magnitude & threshold graph ##################################################
		self.mag_graph = Canvas(self.root, width=self.CANVAS_W, height=self.CANVAS_H, bg='white')
		self.mag_graph.pack(side=TOP)

		self.threshold_line = self.mag_graph.create_line(0, 0, self.CANVAS_W, 0,
		                                                 fill='#005b96', dash='-', width=2)
		self.set_threshold(25)

		#### control panel ##################################################
		controls = Frame(window)
		controls.pack(fill=X)

		self.rewind_btn = Button(controls, text='Rewind', command=self.rewind_button)
		self.rewind_btn.pack(side=LEFT, ipady=10, ipadx=20)

		self.play_btn = Button(controls, text='Play', command=self.play_wav)
		self.play_btn.pack(side=LEFT, ipady=10, ipadx=20)

		self.record_btn = Button(controls, text='Record', command=self.record_button)
		self.record_btn.pack(side=LEFT, ipady=10, ipadx=20)

		self.save_btn = Button(controls, text='Save', command=self.save_wav)
		self.save_btn.pack(side=LEFT, ipady=10, ipadx=20)

		self.load_wav('../sound/test.wav') # TESTING
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

	def move_cursor(self, cursor, x):
		self.pitch_graph.coords(cursor, [x, 0, x, self.CANVAS_H])
		self.pitch_graph.update_idletasks()

	def animate_cursor(self):
		if self.stream.is_active():
			x = self.CANVAS_W * ((time.clock() - self.play_t) / self.wav.duration + self.start_ratio)
			self.move_cursor(self.cursor_line, x)
			self.root.after(20, self.animate_cursor)
		else:
			self.move_cursor(self.cursor_line, 0)

	def set_threshold(self, value):
		value = self.CANVAS_H - value
		self.mag_graph.coords(self.threshold_line, [0, value, self.CANVAS_W, value])

	def load_wav(self, file_name):
		if self.wf is not None:
			self.wf.close()
		self.wf = wave.open(file_name, 'rb')

		# Open non-binary wave file and get pitch and magnitude.
		self.wav = audio.Audio(path=file_name, sr=11025)
		self.pitch, self.mag = self.wav.pitch_mag()
		self.wf.rewind()
		# Draw the pitch and magnitude.
		x = np.linspace(0, self.CANVAS_W, self.pitch.size)
		self.draw_curve(self.pitch_graph, x, self.pitch)
		self.draw_curve(self.mag_graph, x, self.mag)

	def save_wav(self):
		pass

	def play_wav(self):
		# Stop playback if there is one, and rewind to starting position.
		if self.stream is not None:
			self.stream.stop_stream()
			self.stream.close()
		self.wf.setpos(int(self.wf.getnframes() * self.start_ratio))

		self.stream = self.pyaudio.open(
			rate=self.wf.getframerate(),
			channels=1,
			format=self.pyaudio.get_format_from_width(self.wf.getsampwidth()),
			output=True,
			stream_callback=self.play_callback
		)
		self.root.after(0, self.animate_cursor)
		self.play_t = time.clock()

	def play_callback(self, in_data, frame_count, time_info, status):
		data = self.wf.readframes(frame_count)
		return (data, pyaudio.paContinue)

	def record_wav(self):
		if self.wf is not None:
			self.wf.close()
		self.wf = wave.open(self.TEMP_WAV, 'wb')
		self.wf.setnchannels(1)
		self.wf.setsampwidth(self.pyaudio.get_sample_size(pyaudio.paInt16))
		self.wf.setframerate(self.RECORD_RATE)

		self.stream = self.pyaudio.open(
			rate=self.RECORD_RATE,
			channels=1,
			format=pyaudio.paInt16,
			input=True,
			stream_callback=self.record_callback
		)

	def record_callback(self, in_data, frame_count, time_info, status):
		self.wf.writeframes(in_data)
		return (None, pyaudio.paContinue)

	def placeholder(self):
		pass

	########### Menu Options ############
	def open_wav_file(self):
		path = filedialog.askopenfilename(title='Select wav file', filetypes=(("wav file","*.wav"),))
		if len(path) > 0:
			self.load_wav(path)

	###########    Buttons   ############
	def record_button(self):
		if self.recording:
			self.stream.stop_stream()
			self.stream.close()
			self.load_wav(self.TEMP_WAV)
			self.recording = False
		else:
			self.record_wav()
			self.recording = True

	def rewind_button(self):
		if self.stream and self.stream.is_active():
				self.stream.stop_stream()
		self.move_cursor(self.cursor_line, 0)
		self.move_cursor(self.cursor_start_line, 0)
		self.start_ratio = 0

	########### Mouse Events ############
	# Move cursor and stop audio if playing.
	def click_playback_cursor(self, event):
		if self.wf is not None:
			if self.stream and self.stream.is_active():
				self.stream.stop_stream()

			self.move_cursor(self.cursor_start_line, event.x)
			self.start_ratio = event.x / self.CANVAS_W