## AUTHOR:         Aaron Nicolson
## AFFILIATION:    Signal Processing Laboratory, Griffith University
##
## This Source Code Form is subject to the terms of the Mozilla Public
## License, v. 2.0. If a copy of the MPL was not distributed with this
## file, You can obtain one at http://mozilla.org/MPL/2.0/.

# from dev.acoustic.analysis_synthesis.polar import synthesis
# from dev.acoustic.feat import polar
# from dev.ResNet import ResNet
# import dev.optimisation as optimisation
# import numpy as np
# import tensorflow as tf

from deepxi.network.cnn import TCN
from deepxi.sig import DeepXiInput
from deepxi.utils import read_wav
from scipy.io import savemat
from tensorflow.keras.layers import Input
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tqdm import tqdm
import deepxi.se_batch as batch
import math, os, pickle, random
import numpy as np
import tensorflow as tf

class DeepXi(DeepXiInput):
	"""
	Deep Xi
	"""
	def __init__(
		self, 
		N_w, 
		N_s, 
		NFFT, 
		f_s, 
		mu=None, 
		sigma=None, 
		network='TCN', 
		min_snr=None, 
		max_snr=None, 
		save_dir=None
		):
		"""
		Argument/s
			Nw - window length (samples).
			Ns - window shift (samples).
			NFFT - number of DFT bins.
			f_s - sampling frequency.
			mu - sample mean of each instantaneous a priori SNR in dB frequency component.
			sigma - sample standard deviation of each instantaneous a priori SNR in dB frequency component.
			network - network type.
			min_snr - minimum SNR level for training.
			max_snr - maximum SNR level for training.
			save_dir - directory to save model.
		"""
		super().__init__(N_w, N_s, NFFT, f_s, mu, sigma)
		self.min_snr = min_snr
		self.max_snr = max_snr
		self.save_dir = save_dir
		self.n_feat = math.ceil(self.NFFT/2 + 1)
		self.n_outp = self.n_feat
		self.inp = Input(name='inp', shape=[None, self.n_feat], dtype='float32')


# tf.keras.layers.Masking(
#     mask_value=0.0, **kwargs
# )

		if network == 'TCN': self.network = TCN(self.inp, self.n_outp, B=40, d_model=256, d_f=64, k=3, max_d_rate=16, softmax=False)
		else: raise ValueError('Invalid network type.')

		self.opt = Adam()
		self.model = Model(inputs=self.inp, outputs=self.network.outp)
		self.model.summary()
		if self.save_dir == None: self.save_dir = 'model'
		if not os.path.exists(self.save_dir): os.makedirs(self.save_dir)
		with open(self.save_dir + "/model.json", "w") as json_file: json_file.write(self.model.to_json())

	def save_weights(self, epoch):
		""" 
		"""
		self.model.save_weights(self.save_dir + "/epoch-" + str(epoch))

	def load_weights(self, epoch):
		""" 
		"""
		self.model.load_weights(self.save_dir + "/epoch-" + str(epoch))

	def get_stats(self, stats_path, sample_size, train_s_list, train_d_list):
		"""
		"""
		if os.path.exists(stats_path + '/stats.p'):
			print('Loading sample statistics...')
			with open(stats_path + '/stats.p', 'rb') as f:
				stats = pickle.load(f)
				self.mu = stats['mu_hat']
				self.sigma = stats['sigma_hat']
		elif train_s_list == None:
			raise ValueError('No stats.p file exists. data/stats.p is available here: https://github.com/anicolson/DeepXi/blob/master/data/stats.p.')
		else:
			print('Finding sample statistics...')
			random.shuffle(train_s_list) # shuffle list.
			s_sample, s_sample_seq_len = batch.Clean_mbatch(train_s_list, sample_size, 0, sample_size) 
			d_sample, d_sample_seq_len = batch.Noise_mbatch(train_d_list, sample_size, s_sample_seq_len) 
			snr_sample = np.random.randint(self.min_snr, self.max_snr + 1, sample_size)
			samples = []
			for i in tqdm(range(s_sample.shape[0])):
				xi, _ = self.instantaneous_a_priori_snr_db(s_sample[i:i+1], d_sample[i:i+1], s_sample_seq_len[i:i+1], 
					d_sample_seq_len[i:i+1], snr_sample[i:i+1])
				samples.append(xi.numpy())
			samples = np.vstack(samples)
			if len(samples.shape) != 2: raise ValueError('Incorrect shape for sample.')
			stats = {'mu_hat': np.mean(samples, axis=0), 'sigma_hat': np.std(samples, axis=0)}
			if not os.path.exists(stats_path): os.makedirs(stats_path)
			with open(stats_path + '/stats.p', 'wb') as f: pickle.dump(stats, f)
			savemat(stats_path + '/stats.m', mdict={'mu_hat': stats['mu_hat'], 'sigma_hat': stats['sigma_hat']})
			print('Sample statistics saved to pickle file.')

	def train(
		self, 
		train_s_list, 
		train_d_list, 
		mbatch_size=8, 
		max_epochs=200, 
		ver='VERSION_NAME',
		stats_path=None, 
		sample_size=None,
		resume=False,
		start_epoch=None
		):
		"""
		"""
		self.train_s_list = train_s_list
		self.train_d_list = train_d_list
		self.mbatch_size = mbatch_size
		self.n_examples = len(self.train_s_list)
		self.n_iter = math.ceil(self.n_examples/mbatch_size)

		self.get_stats(stats_path, sample_size, train_s_list, train_d_list)
		train_dataset = self.dataset()

		if resume: self.load_weights(self.save_dir, start_epoch)
		else: start_epoch = 0

		if not os.path.exists("log"): os.makedirs("log") # create log directory.
		if not os.path.exists("log/" + ver + ".csv"):
			with open("log/" + ver + ".csv", "a") as results:
				results.write("Epoch, Train loss, Val. loss, D/T\n")

		# pbar = tqdm(total=args.max_epochs, desc='Training E' + str(start_epoch))
		# pbar.update(start_epoch-1)
		# for i in range(start_epoch, args.max_epochs+1):
			
		self.model.compile(loss='binary_crossentropy', optimizer=self.opt)

		history = self.model.fit(train_dataset, initial_epoch=start_epoch, epochs=max_epochs, steps_per_epoch=self.n_iter)
		

		# val_loss = model.loss(x_val, y_val, x_val_len, y_val_len, batch_size=args.mbatch_size)
		# likelihood = model.output([x_val], batch_size=args.mbatch_size)
		# _, cer = model.greedy_decode_metrics(likelihood, y_val, x_val_len, y_val_len, args.idx2char)
		# pbar.set_description_str("E%d train|val loss: %.2f|%.2f, val CER: %.2f%%" % (i, 
		# 	history.history['loss'][0], val_loss, 100*cer))
		# pbar.update(); pbar.refresh()
		# with open("log/" + args.ver + ".csv", "a") as results:
		# 	results.write("%d, %.2f, %.2f, %.2f, %s\n" % (i, 
		# 		history.history['loss'][0], val_loss, 100*cer,
		# 		datetime.now().strftime('%Y-%m-%d/%H:%M:%S')))
		# model.save_weights(args.model_path, i)
			

	def infer(): 
		"""
		"""
		pass

	def dataset(self, buffer_size=16):
		"""
		"""
		dataset = tf.data.Dataset.from_generator(
			self.mbatch_gen, 
			(tf.float32, tf.float32), 
			(tf.TensorShape([None, None, self.n_feat]), 
			tf.TensorShape([None, None, self.n_outp])))
		dataset = dataset.prefetch(buffer_size) 
		return dataset

	def mbatch_gen(self): 
		"""
		"""
		random.shuffle(self.train_s_list)
		start_idx, end_idx = 0, self.mbatch_size
		for _ in range(self.n_iter):
			s_mbatch_list = self.train_s_list[start_idx:end_idx] # get mini-batch list from training list.
			d_mbatch_list = random.sample(self.train_d_list, end_idx-start_idx) # get mini-batch list from training list.
			max_len = max([dic['seq_len'] for dic in s_mbatch_list]) # find maximum length wav in mini-batch.
			s_mbatch = np.zeros([len(s_mbatch_list), max_len], np.int16) # numpy array for wav matrix.
			d_mbatch = np.zeros([len(s_mbatch_list), max_len], np.int16) # numpy array for wav matrix.
			s_mbatch_len = np.zeros(len(s_mbatch_list), np.int32) # list of the wavs lengths.
			for i in range(len(s_mbatch_list)):
				(wav, _) = read_wav(s_mbatch_list[i]['file_path']) # read wav from given file path.		
				s_mbatch[i,:s_mbatch_list[i]['seq_len']] = wav # add wav to numpy array.
				s_mbatch_len[i] = s_mbatch_list[i]['seq_len'] # append length of wav to list.
				flag = True
				while flag:
					if d_mbatch_list[i]['seq_len'] < s_mbatch_len[i]: d_mbatch_list[i] = random.choice(self.train_d_list)
					else: flag = False
				(wav, _) = read_wav(d_mbatch_list[i]['file_path']) # read wav from given file path.
				rand_idx = np.random.randint(0, 1+d_mbatch_list[i]['seq_len']-s_mbatch_len[i])
				d_mbatch[i,:s_mbatch_len[i]] = wav[rand_idx:rand_idx+s_mbatch_len[i]] # add wav to numpy array.
			d_mbatch_len = s_mbatch_len
			snr_mbatch = np.random.randint(self.min_snr, self.max_snr+1, end_idx-start_idx) # generate mini-batch of SNR levels.
			x_STMS, xi_bar, _ = self.training_example(s_mbatch, d_mbatch, s_mbatch_len, d_mbatch_len, snr_mbatch)
			start_idx += self.mbatch_size; end_idx += self.mbatch_size
			if end_idx > self.n_examples: end_idx = self.n_examples
			yield x_STMS, xi_bar

	def Clean_mbatch(clean_list, mbatch_size, start_idx, end_idx):
		'''
		Creates a padded mini-batch of clean speech wavs.

		Inputs:
			clean_list - training list for the clean speech files.
			mbatch_size - size of the mini-batch.
			version - version name.

		Outputs:
			mbatch - matrix of paded wavs stored as a numpy array.
			seq_len - length of each wavs strored as a numpy array.
			clean_list - training list for the clean files.
		'''

		return mbatch, np.array(seq_len, np.int32)

	def Noise_mbatch(noise_list, mbatch_size, clean_seq_len):
		'''
		Creates a padded mini-batch of noise speech wavs.

		Inputs:
			noise_list - training list for the noise files.
			mbatch_size - size of the mini-batch.
			clean_seq_len - sequence length of each clean speech file in the mini-batch.

		Outputs:
			mbatch - matrix of paded wavs stored as a numpy array.
			seq_len - length of each wavs strored as a numpy array.
		'''
		
		return mbatch, np.array(seq_len, np.int32)
