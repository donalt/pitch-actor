import numpy as np
import librosa as rosa
import soundfile as sf
import math

class Synth():
	SAMPLE_RATE = 11025
	SPEED_UP = 1.1 # Speed up voice playback.

	def __init__(self):
		self.voice = None

	def load_voice(self, path, freq):
		self.voice, self.voice_sr = sf.read(path, dtype='float32')
		self.voice_f = freq

	def prepare(self, pitch, vol, sr):
		if self.voice is None:
			raise RuntimeError('voice is not loaded')
		
		samples = pitch.size - 1 # Final sample is only for interpolation.
		self.f_per_sample = int(self.SAMPLE_RATE / (sr * self.SPEED_UP)) # Frames per pitch and vol sample.

		self.pitch = pitch
		self.vol = vol
		self.out = np.empty(samples * self.f_per_sample, dtype='float32')
		self.vi = 0.0 # Current index of voice.
		self.li = 0   # Index of pitch/vol.
		self.t = 0 # Index of the output voiceline.

	def voice_forward(self, samples):
		"""Synthesise <samples> more samples for the output.
		"""
		# Make sure that samples is divisble by f_per_sample. 
		rem = samples % self.f_per_sample
		if rem > 0:
			samples += self.f_per_sample - rem

		end_t = min(self.t + samples, len(self.out))
		if self.t == end_t: # Already finished building.
			return

		voice = self.voice # Base "voice" described with array of floats.
		pitch = self.pitch # Pitch array (int)
		vol   = self.vol   # Volume array (float), same length as pitch.

		vi_max = len(voice)
		step_size = self.voice_sr / self.SAMPLE_RATE
		sample_use = 0 # Times the current sample has been used.

		for t in range(self.t, end_t):
			# Sample the base wav and scale by volume.
			vi_floor = int(math.floor(self.vi))
			vi_ceil  = 0 if (vi_floor + 1 == vi_max) else (vi_floor + 1)
			target_vol = lerp(vol[self.li], vol[self.li+1], sample_use / self.f_per_sample)
			self.out[t] = target_vol * lerp(voice[vi_floor], voice[vi_ceil], self.vi - vi_floor)
			
			# Step forward in base wav, taking pitch into account.
			target_f = lerp(pitch[self.li], pitch[self.li+1], sample_use / self.f_per_sample)
			self.vi += step_size * (target_f / self.voice_f)	
			self.vi = self.vi % vi_max # Base voice is cyclic.

			# Move closer to next pitch/vol sample.
			sample_use += 1
			if sample_use == self.f_per_sample:
				sample_use = 0
				self.li += 1
		self.t = end_t

	def duration(self):
		"""How many seconds the output voiceline is or will be."""
		return self.out.size / self.SAMPLE_RATE

	def samples(self, a=-1, b=-1):
		"""If a or b is not given, return amount of samples in full line.
		   If given, return samples in range [a, b)."""
		if a == -1 or b == -1:
			return self.out.size
		return self.out[a:b]

	def duration(self):
		"""How many seconds the output voiceline is or will be."""
		return self.out.size / self.SAMPLE_RATE

def lerp(a, b, t):
	return (1-t)*a + t*b

def gen_sine(freq, sr, path):
	sine = rosa.tone(frequency=freq, sr=sr, length=sr).astype(np.float32)
	sf.write(path, sine, sr, 'FLOAT')