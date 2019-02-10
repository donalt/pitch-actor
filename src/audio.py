import librosa as rosa
import pyaudio
import numpy as np
from struct import unpack

class Audio():
	def __init__(self, path=None, binary=None, sr=11025):
		if path is not None:
			self.y, _ = rosa.load(path, sr=sr)
		elif binary is not None:
			self.y = binwav2dec(binary)
		else:
			raise ValueError('path or binary needs to be set')

		self.sr = sr
		self.samples = self.y.size
		self.duration = self.samples / self.sr # Length in seconds.

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

def binwav2dec(bin_data):
	npts = int(len(bin_data)/2)
	formatstr = '%ih' % npts
	return np.array(unpack(formatstr, bin_data)) / 32768