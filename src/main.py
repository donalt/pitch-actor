import librosa as rosa
import numpy as np
import matplotlib.pyplot as plt

def dft(x):
	# Indices and sizes.
	N = x.size
	i = np.arange(0, N)
	k = np.arange(0, N//2 + 1)
	
	reX = np.empty(k.size)
	imX = np.empty(k.size)

	# Analysis equation (decomposition).
	freq = (2*np.pi/N) * i
	for a in k:
		reX[a] =  x.dot(np.cos(freq * a))
		imX[a] = -x.dot(np.sin(freq * a))

	return reX, imX

def idft(reX, imX):
	# From spectral density to amplitudes.
	N = (reX.size-1) * 2
	imX = -imX/ (N/2)
	reX = reX/ (N/2)
	reX[0] /= 2
	reX[-1]/= 2
	
	k = np.arange(0, N/2 + 1)
	xk = np.linspace(0, np.pi, reX.size)
	
	# Synthesis!
	out = np.zeros(N)
	for i in range(N):
		out[i]  = reX.dot(np.cos(xk * i)) + \
		          imX.dot(np.sin(xk * i))
	return out

def plot_dft(y, reX, imX):
	N = (reX.size-1) * 2
	c = (2*np.pi/N)

	_, axs = plt.subplots(2, 2)
	x = np.arange(0, N)

	re_sum = np.zeros(N)
	im_sum = np.zeros(N)

	# Sum together reX and imX separetely.
	for i in range(reX.size):
		re_sum += reX[i] * np.cos((c*i) * x)
	for i in range(imX.size):
		im_sum += imX[i] * np.sin((c*i) * x)

	f =  np.linspace(0, 0.5 * 16000, N)
	# Input x
	axs[0,0].plot(y, 'k')
	# Frequency spectrum
	axs[1,0].plot(f, np.log(magnitude(reX, imX)), 'k')
	
	plt.show()

def plot_spectrum(reX, imX):
	f = np.linspace(0, 0.5 * 16000, reX.size)
	plt.figure(figsize=(10, 2))
	plt.plot(f, 20 * np.log10(magnitude(reX, imX)), 'k')
	plt.xlim(0, f[-1])
	plt.tight_layout()
	plt.show()

# Convert from rectangular to polar notation.
def magnitude(reX, imX):
	return np.sqrt(reX**2 + imX**2)

def phase(reX, imX):
	return np.arctan(imX / reX)


def main2():
	x, _ = rosa.load('test.wav', sr=16000)
	x = x[3000:3512]

	reX, imX = dft(x)
	plot_spectrum(reX, imX)
	#rmse = rosa.feature.rmse(y)
	
	#y_r = np.flip(y)
	#even = (y + y_r) / 2
	#odd  = (y - y_r) / 2

	#_, axs = plt.subplots(5, 1, True)
	#axs[0].plot(y, 'k')
	#axs[1].plot(even + odd, 'k')
	#axs[2].plot(even, 'r')
	#axs[3].plot(odd, 'b')
	#x = np.linspace(0, 1, 100)
	#c = 2 * np.pi
	#freq = [0, 1, 2, 3, 4]
	#for i, f in enumerate(freq):
	#	axs[i].plot(x, np.cos(x * (c * f)))
	#plt.plot(np.linspace(0, y.size, rmse.size), rmse.T, 'r')
	#print(y[:100])

def main():
	sr = 5512
	y, _ = rosa.load('../sound/test.wav', sr=sr)
	samples = y.size
	duration = samples / sr # Length in seconds.

	n_fft = 1024 # Window size
	hop_length = 256 # Move window by this amount
	windows = int(np.ceil(samples / hop_length))
	window_time = n_fft / sr
	t_between_samples = hop_length / sr

	fmin, fmax = 20, 300
	threshold = 25 # Magnitude threshold

	# TODO: get S from rosa.stft() first.
	pitches, mag = rosa.piptrack(y, sr, None, n_fft, hop_length, fmin, fmax)

	pitch = np.empty(windows)
	magnitude = np.empty(windows)
	for t in range(windows):
		max_i = mag[:, t].argmax()
		magnitude[t] = mag[max_i, t]
		pitch[t] = pitches[max_i, t]

		if (magnitude[t] < threshold):
			pitch[t] = None

	plt.plot(pitch, 'r')
	plt.plot(magnitude, 'k')
	plt.plot([0, pitch.size], [threshold, threshold], 'b--')
	plt.tight_layout()
	plt.show()

if __name__ == '__main__':
	main()
