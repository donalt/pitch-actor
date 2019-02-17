import numpy as np
import librosa as rosa
import pyaudio
import wave
import time
from struct import unpack, pack

MIN_FREQ = 30
MAX_FREQ = 350

class Audio():
	RECORD_RATE = 11025
	
	TEMP_WAV = 'tmp.wav' # Where to save recordings.

	FRAME_LEN = 1024
	HOP_LEN = 512
	CURSOR_OFFSET = 0.1 # How many seconds to delay the playback cursor.

	def __init__(self, gui, synth):
		self.gui = gui
		self.synth = synth
		self.pyaudio = pyaudio.PyAudio()
		self.wf = None     # The loaded binary .wav file.
		self.y = None      # wav file in floats.
		self.stream = None # Stream used when playing and recording wav.
		self.start_ratio = 0 # [0,1] from where to start playback.
		self._recording = False
		self.pitch_shift = 12

	def _load_audio(self, path=None, binary=None):
		if path is not None:
			self.y, _ = rosa.load(path, sr=self.RECORD_RATE)
		elif binary is not None:
			self.y = bin2dec(binary)
		else:
			raise ValueError('path or binary needs to be set')

		self.sr = self.RECORD_RATE
		self.samples = self.y.size

	def load_wav(self, file_name):
		if self.wf is not None:
			self.wf.close()
		self.wf = wave.open(file_name, 'rb')
		# Open non-binary wave file.
		self._load_audio(path=file_name)
		# Get the RMS (volume).
		vol = rosa.feature.rmse(y=self.y, frame_length=self.FRAME_LEN, hop_length=self.HOP_LEN).flatten()
		# Get pitch.
		pitch = self.calc_pitch(MIN_FREQ, MAX_FREQ)
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
		self.duration = self.samples / self.sr # Length in seconds.
		self.play_time = time.clock()

	def _play_callback(self, in_data, frame_count, time_info, status):
		data = self.wf.readframes(frame_count)
		return (data, pyaudio.paContinue)

	def play_voice(self, pitch, vol, dirty):
		self._close_stream()
		# Start resynthesising voice if pitch/vol has changed.
		if dirty:
			self.synth.prepare(pitch * 3, vol, self.pitch_sr)

		# Start playing the synthesised voice.
		self.play_i = 0
		self.stream = self.pyaudio.open(
			rate=self.RECORD_RATE,
			channels=1,
			format=self.pyaudio.get_format_from_width(2),
			output=True,
			stream_callback=self._pitch_callback
		)
		self.duration = self.synth.duration()
		self.play_time = time.clock()

	def _pitch_callback(self, in_data, frame_count, time_info, status):
		self.synth.voice_forward(int(frame_count * 1.5))
		b = min(self.play_i + frame_count, self.synth.samples())
		data = dec2bin(self.synth.samples(self.play_i, b))
		self.play_i = b
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

	def calc_pitch(self, fmin, fmax):
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
