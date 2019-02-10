import librosa as rosa
import numpy as np
#import matplotlib.pyplot as plt

class Audio():
	def __init__(self, file_path, sr=5512):
		self.sr = sr
		self.y, _ = rosa.load(file_path, sr=sr)
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

		# plt.plot(pitch, 'r')
		# plt.plot(magnitude, 'k')
		# plt.plot([0, pitch.size], [threshold, threshold], 'b--')
		# plt.tight_layout()
		# plt.show()
		return pitch, magnitude
