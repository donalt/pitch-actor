import numpy as np
import librosa as rosa
import pyaudio
import soundfile as sf
import wave
import time
import math
from struct import unpack, pack

SPEED_UP = 1.2 # Speed up rate of pitch preview.

class Audio():
	RECORD_RATE = 11025
	
	TEMP_WAV = 'tmp.wav'

	FRAME_LEN = 1024
	HOP_LEN = 512
	CURSOR_OFFSET = 0.1 # How many seconds to delay the playback cursor.

	def __init__(self, gui):
		self.gui = gui
		self.pyaudio = pyaudio.PyAudio()
		self.wf = None     # The loaded binary .wav file.
		self.y = None      # wav file in floats.
		self.stream = None # Stream used when playing and recording wav.
		self.start_ratio = 0 # [0,1] from where to start playback.
		self._recording = False
		self.pitch_shift = 12

		# sine, sr = sf.read('../sound/sine220.wav', dtype='float32')
		# pitch = np.linspace(440, 880, 60)
		# vol = np.ones(60) * 0.2
		# y = build_voiceline(sine, 220, sr, pitch, vol, 30, self.RECORD_RATE)
		# self.save_wav(y, 'voiceline.wav', self.RECORD_RATE)
		# exit()

	def _load_audio(self, path=None, binary=None):
		if path is not None:
			self.y, _ = rosa.load(path, sr=self.RECORD_RATE)
		elif binary is not None:
			self.y = bin2dec(binary)
		else:
			raise ValueError('path or binary needs to be set')

		self.sr = self.RECORD_RATE
		self.samples = self.y.size
		self.duration = self.samples / self.sr # Length in seconds.

	def load_wav(self, file_name):
		if self.wf is not None:
			self.wf.close()
		self.wf = wave.open(file_name, 'rb')
		# Open non-binary wave file.
		self._load_audio(path=file_name)
		# Get the RMS (volume).
		vol = rosa.feature.rmse(y=self.y, frame_length=self.FRAME_LEN, hop_length=self.HOP_LEN).flatten()
		# Get pitch.
		pitch = self.calc_pitch()
		if vol.size != pitch.size:
			vol = vol[:-1]

		self.wf.rewind()
		self.gui.draw_graph(pitch, vol)

	def save_wav(self, y, path, sr):
		wf = wave.open(path, 'wb')
		wf.setnchannels(1)
		wf.setsampwidth(self.pyaudio.get_sample_size(pyaudio.paInt16))
		wf.setframerate(sr)
		wf.writeframes(dec2bin(y))
		wf.close()

	def play(self):
		self._close_stream()
		self.wf.setpos(int(self.wf.getnframes() * self.start_ratio))

		self.stream = self.pyaudio.open(
			rate=self.wf.getframerate(),
			channels=1,
			format=self.pyaudio.get_format_from_width(self.wf.getsampwidth()),
			output=True,
			stream_callback=self._play_callback
		)
		self.play_time = time.clock()

	def _play_callback(self, in_data, frame_count, time_info, status):
		data = self.wf.readframes(frame_count)
		return (data, pyaudio.paContinue)

	def play_pitch(self, pitch, vol):
		self._close_stream()

		sine, sr = sf.read('../sound/sine220.wav', dtype='float32')
		# pitch = np.linspace(440, 880, 60)
		p = np.copy(pitch)
		p[p == -1] = 0
		#vol = np.ones(pitch.size) * 0.5
		#print(vol)
		y = build_voiceline(sine, 220, sr, p*3, vol, self.pitch_sr*SPEED_UP, self.RECORD_RATE)
		#self.voice = dec2bin(y)
		self.save_wav(y, 'voiceline.wav', self.RECORD_RATE)
		return
		self.stream = self.pyaudio.open(
			rate=self.RECORD_RATE,
			channels=1,
			format=self.pyaudio.get_format_from_width(4),
			output=True,
			stream_callback=self._pitch_callback
		)
		self.play_time = time.clock()

	def _pitch_callback(self, in_data, frame_count, time_info, status):
		data = 0 # TODO: Play preview directly in-app.
		return (data, pyaudio.paContinue)

	def stop_recording(self):
		self._close_stream()
		self.load_wav(self.TEMP_WAV)
		self._recording = False

	def start_recording(self):
		self._close_stream()
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
			stream_callback=self._record_callback
		)
		self._recording = True

	def _record_callback(self, in_data, frame_count, time_info, status):
		self.wf.writeframes(in_data)
		return (None, pyaudio.paContinue)

	def _close_stream(self):
		if self.stream is not None:
			self.stream.stop_stream()
			self.stream.close()
			self.stream = None

	def stop(self):
		if self.stream and self.stream.is_active():
			self.stream.stop_stream()

	def rewind(self):
		self.start_ratio = 0
		self.stop()

	def calc_pitch(self, fmin=20, fmax=300):
		windows = int(np.ceil(self.samples / self.HOP_LEN))
		pitches, mag = rosa.piptrack(self.y, self.sr, None, self.FRAME_LEN, self.HOP_LEN, fmin, fmax)

		pitch = np.empty(windows)
		for t in range(windows):
			max_i = mag[:, t].argmax()
			pitch[t] = pitches[max_i, t]
		self.pitch_sr = self.sr * (pitch.size / self.y.size)
		return pitch

	#### Getters ####
	def loaded(self):
		return self.wf is not None

	def playing(self):
		return self.stream.is_active()

	def recording(self):
		return self._recording

	def play_ratio(self):
		play_time = time.clock() - self.play_time - self.CURSOR_OFFSET
		return (play_time / self.duration) + self.start_ratio

	#### Setters ####
	def set_start(self, start_ratio):
		self.start_ratio = start_ratio

# TODO: use Struct(format) to compile formatstr once.
def bin2dec(bin_data):
	npts = int(len(bin_data)/2)
	formatstr = '%ih' % npts
	return np.array(unpack(formatstr, bin_data)) / 32768 # 16 bit data.

def dec2bin(dec_data):
	npts = int(len(dec_data))
	formatstr = '%ih' % npts
	return pack(formatstr, *(dec_data * 32768).astype(np.int16))

def gen_sine(freq, sr, path):
	sine = rosa.tone(frequency=freq, sr=sr, length=sr).astype(np.float32)
	sf.write(path, sine, sr, 'FLOAT')

def gate(array, test, threshold):
	a = np.copy(array)
	a[test < threshold] = -1
	return a

# librosa source code
def shift_pitch(y, sr, n_steps, bins_per_octave=12):
	rate = 2.0 ** (-float(n_steps) / bins_per_octave)
	# Stretch in time, then resample
	y_shift = rosa.core.resample(rosa.effects.time_stretch(y, rate), float(sr) / rate, sr)
	# Crop to the same dimension as the input
	return rosa.util.fix_length(y_shift, len(y))

def build_voiceline(base_wav, base_f, base_sr, pitch, vol, in_sr, out_sr):
	"""Build a wav with pitch and volume modulations imposed on a base wav.

	base_wav : Base "voice" described with array of floats.
	base_f   : The frequency of base wav, assumed to be constant.
	base_sr  : Sampling rate of base wav.
	
	pitch  : Pitch array (int)
	vol    : Volume array (float), same length as pitch.
	in_sr  : Sampling rate of pitch and vol.

	out_sr : Sampling rate of the output voiceline.
	"""
	if len(pitch) != len(vol):
		raise ValueError('pitch and vol not same length')

	bt = 0.0 # base time: Current index of base wav.
	bt_max = len(base_wav)
	step_size = base_sr / out_sr

	i = 0 # Index of pitch and vol.
	i_max = len(pitch) - 1 # Final sample is only for interpolation.
	f_per_sample = int(out_sr / in_sr) # Frames per pitch and vol sample.
	sample_use = 0 # Times the current sample has been used.

	y = np.empty(f_per_sample * i_max, dtype='float32')
	for t in range(len(y)):
		# Sample the base wav and scale by volume.
		# TODO: interpolate volume
		floor = int(math.floor(bt))
		ceil  = int(math.ceil(bt))
		ceil_bt = ceil if ceil < bt_max else 0
		target_vol = lerp(vol[i], vol[i+1], sample_use / f_per_sample)
		y[t] = target_vol * lerp(base_wav[floor], base_wav[ceil_bt], bt - floor)
		
		# Step forward in base wav, taking pitch into account.
		target_f = lerp(pitch[i], pitch[i+1], sample_use / f_per_sample)
		bt += step_size * (target_f / base_f)	
		bt = bt % bt_max # Base wav is cyclic.

		# Move closer to next pitch/vol sample.
		sample_use += 1
		if sample_use == f_per_sample:
			sample_use = 0
			i += 1
	return y

def lerp(a, b, t):
	return (1-t)*a + t*b