import numpy as np
import librosa as rosa
import pyaudio
import wave
import time
from struct import unpack

class Audio():
	RECORD_RATE = 11025
	TEMP_WAV = 'tmp.wav'
	CURSOR_OFFSET = 0.1 # How many seconds to delay the playback cursor.

	def __init__(self, gui):
		self.gui = gui
		self.pyaudio = pyaudio.PyAudio()
		self.wf = None     # The loaded binary .wav file.
		self.stream = None # Stream used when playing and recording wav.
		self.start_ratio = 0 # [0,1] from where to start playback.
		self._recording = False

	def _load_audio(self, path=None, binary=None, sr=11025):
		if path is not None:
			self.y, _ = rosa.load(path, sr=sr)
		elif binary is not None:
			self.y = binwav2dec(binary)
		else:
			raise ValueError('path or binary needs to be set')

		self.sr = sr
		self.samples = self.y.size
		self.duration = self.samples / self.sr # Length in seconds.

	def load_wav(self, file_name):
		if self.wf is not None:
			self.wf.close()
		self.wf = wave.open(file_name, 'rb')
		# Open non-binary wave file and get pitch and magnitude.
		self._load_audio(path=file_name, sr=11025)
		self.pitch, self.mag = self.pitch_mag()
		self.wf.rewind()
		self.gui.draw_pitch_mag(self.pitch, self.mag)

	def play(self):
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
			stream_callback=self._play_callback
		)
		self.play_time = time.clock()

	def _play_callback(self, in_data, frame_count, time_info, status):
		data = self.wf.readframes(frame_count)
		return (data, pyaudio.paContinue)

	def stop_recording(self):
		self.stream.stop_stream()
		self.stream.close()
		self.load_wav(self.TEMP_WAV)
		self._recording = False

	def start_recording(self):
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

	def stop(self):
		if self.stream and self.stream.is_active():
			self.stream.stop_stream()

	def rewind(self):
		self.start_ratio = 0
		self.stop()

	def pitch_mag(self, n_fft=1024, hop_length=256, fmin=20, fmax=300, threshold=25):
		self.threshold = threshold
		windows = int(np.ceil(self.samples / hop_length))
		window_time = n_fft / self.sr
		t_between_samples = hop_length / self.sr

		# TODO: get S from rosa.stft() first.
		pitches, mag = rosa.piptrack(self.y, self.sr, None, n_fft, hop_length, fmin, fmax)

		pitch = np.empty(windows)
		magnitude = np.empty(windows)
		for t in range(windows):
			max_i = mag[:, t].argmax()
			magnitude[t] = mag[max_i, t]
			pitch[t] = pitches[max_i, t]

			if (magnitude[t] < threshold):
				pitch[t] = None

		return pitch, magnitude

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

def binwav2dec(bin_data):
	npts = int(len(bin_data)/2)
	formatstr = '%ih' % npts
	return np.array(unpack(formatstr, bin_data)) / 32768