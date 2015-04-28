import os, sys

lib_path = os.path.abspath(os.path.join('..','_Libraries'))
sys.path.append(lib_path)

from rlabs_libutils import DataStruct 		# to read data file

import numpy as np
from scipy import signal
import scipy.stats

import matplotlib.pyplot as plt
import itertools

from Tkinter import Tk 						# for open data file GUI
from tkFileDialog import askopenfilenames 	# for open data file GUI

def main():
	
	# # select eyetracker data file
	# Tk().withdraw() 												# we don't want a full GUI, so keep the root window from appearing
	# datafile = askopenfilenames(title='Chose file', 				# show an "Open" dialog box and return the path to the selected file
	# 	initialdir = '..')[0] 
	# ds = DataStruct(datafile) 										# create new DataStruct instance with datafile
	# data = ds.leftgazeXvelocity[ds.leftgazeXvelocity != -1]			# get relevant data

	# define constants --------------------------------------------------------------------------------------------
	pix = 1280
	DPP = 0.03
	framerate = 120.0

	# read data ---------------------------------------------------------------------------------------------------
	data = np.genfromtxt('data.txt') 								# read data
	data_pix = data * pix 											# convert from arbitrary units to pixels
	data_deg = data_pix * DPP 										# convert from pixels to degrees

	# compute velocity ---------------------------------------------------------------------------------------------
	velocity  = np.diff(data_deg,  n=1) * framerate; 				# compute velocity

	# Savitzky-Golay filter. ---------------------------------------------------------------------------------------
	# Parameters: window length and poly order.
	# savgol_plot() will plot the velocity filtered using dfferent window lenghts and diferent polynomial orders.
	# Need to set the window length initial value (odd integer), the initial value of polynomial order, 
	# and the number of windows to compute.

	# define parameters
	wl_array 	= [5, 7, 9, 11] 									# array of window lengths
	po_for_wl 	= 3 	 											# polynomial order used with different window lengths
	po_array 	= [2,3,4]			 								# array of polynomial orders
	wl_for_po 	= 2 * np.floor(np.array(po_array) / 2) + 1 			# array of window lengths to use with different polynomial order values

	savgol_plot(velocity, wl_array, po_for_wl, po_array, wl_for_po) 		

	# Differential filter. -----------------------------------------------------------------------------------------
	# Parameters: bins and divisor.
	# differential_plot() will plot the velocity filtered using different bins and different divisors.
	# For different bins, dvsr_init is used as the fixed divisor.
	# For different divisors, bins_init is used as the fixed bins value.
	# Need to set the initial and maximum values for bins and divisor

	# define parameters
	bins_array 		= [2] 											# array of bins values
	dvsr_for_bins 	= 3 											# divisor value used with different bins values
	dvsr_array 		= [3,4] 										# array of divisors
	bins_for_dvsr 	= 2 											# bins used with different divisors

	differential_plot(data_deg, velocity, bins_array, 				# filter data
		dvsr_for_bins, dvsr_array, bins_for_dvsr)


	plt.show() 														# show plots

def differentialsmoothing(array, bins, divisor, fs = 120.0):
	window = np.hstack((np.ones(bins),0,-np.ones(bins)))
	filteredarray = np.convolve(array, window, 'valid') / (divisor / fs)
	return np.hstack((np.ones((len(array)-len(filteredarray))/2), 
		filteredarray, np.ones((len(array)-len(filteredarray))/2)))

def rgb2hex(color):

	if max(color) <= 1:
		color = (np.array(color) * 255).astype(int).tolist()
	
	r = max(0, min(color[0] , 255))
	g = max(0, min(color[1] , 255))
	b = max(0, min(color[2] , 255))

	return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)

def savgol_plot(velocity, wl_array, po_for_wl, po_array, wl_for_po):
	# compute snr and cv to velocity
	v_snr = 10 * np.log10(scipy.stats.signaltonoise(velocity))	# compute signal to noise ratio
	v_cv = scipy.stats.variation(velocity)        				# compute coefficient of variation
	
	# apply Savitzky-Golay filter
	vfilt_wl = [] 													# initialize: velocity filtered w/ window length
	vfilt_wl_snr = [] 												# to store snr values of v filtered w/ window length
	vfilt_wl_cv = [] 												# to store cv values of v filtered w/ window length

	vfilt_po = [] 													# initialize: velocity filtered w/ polyorder
	vfilt_po_snr = [] 												# to store snr values of v filtered w/ polyorder
	vfilt_po_cv = [] 												# to store cv values of v filtered w/ polyorder

	# filter velocity with different window lengths ---------------------------------------------------------------
	for window_length in wl_array:
		vfwl = signal.savgol_filter(velocity,  						# filter velocity with different window lengths
			window_length, po_for_wl) 								# vfwl: velocity filtered window length

		vf_snr 	= 10 * np.log10(scipy.stats.signaltonoise(vfwl))	# compute signal to noise ratio
		vf_cv 	= scipy.stats.variation(vfwl)        				# compute coefficient of variation

		vfilt_wl.append(vfwl) 										# add filtered signal to array
		vfilt_wl_snr.append(vf_snr) 								# add snr to array
		vfilt_wl_cv.append(vf_cv) 									# add cv to array

	# filter velocity with different poly orders ------------------------------------------------------------------
	new_window_length_array = []
	for polyorder, window_length in itertools.izip(po_array, wl_for_po):

		if window_length <= polyorder:								#
			print 'window length must be odd greater than polyorder. wl = {0}, po = {1}'.format(window_length, polyorder)#
			window_length = int(2 * np.floor(polyorder/2) + 1)		#
			if window_length == polyorder: window_length += 2
			print 'Using window length = {0}'.format(window_length) #

		vfpo = signal.savgol_filter(velocity,  						# filter velocity with different polynomial orders
			window_length, polyorder) 								# vfpo: velocity filtered polynomial order
		
		vf_snr 	= 10 * np.log10(scipy.stats.signaltonoise(vfpo))	# compute signal to noise ratio
		vf_cv 	= scipy.stats.variation(vfpo)        				# compute coefficient of variation
		
		vfilt_po.append(vfpo) 										# add filtered signal to array
		vfilt_po_snr.append(vf_snr) 								# add snr
		vfilt_po_cv.append(vf_cv) 									# add cv

	# plot --------------------------------------------------------------------------------------------------------------
	f1 = plt.figure(1)
	plt.scatter(np.arange(len(velocity)), velocity, label = 'velocity (deg) SNR={0}dB.CV={1}'.format("%.2f" % v_snr,"%.2f" % v_cv))

	for savgol_set, i, snr, cv in itertools.izip(vfilt_wl, wl_array, vfilt_wl_snr, vfilt_wl_cv):
		plt.plot(np.arange(len(savgol_set)), savgol_set, label = 'wl={0}.SNR={1}dB.CV={2}'.format(i,"%.2f" % snr,"%.2f" % cv))

	plt.legend(loc='upper right')
	plt.title('Velocity filtered by Savitzky-Golay. Different window lengths. polyorder = 2')		
	plt.draw()

	f2 = plt.figure(2)
	plt.scatter(np.arange(len(velocity)), velocity, label = 'velocity (deg) SNR={0}dB.CV={1}'.format("%.2f" % v_snr,"%.2f" % v_cv))

	for savgol_set, i, w, snr, cv in itertools.izip(vfilt_po, po_array, wl_for_po, vfilt_po_snr, vfilt_po_cv):
		plt.plot(np.arange(len(savgol_set)), savgol_set, label = 'wl={0},po={1}.SNR={2}dB.CV={3}'.format(w,i,"%.2f" % snr,"%.2f" % cv))

	plt.legend(loc='upper right')			
	plt.title('Velocity filtered by Savitzky-Golay. Different polyorder'.format())		
	plt.draw()

	# plt.show()

	# return 
	vfwl_dict = {'windows lengths': wl_array, 'polyorder': po_for_wl, 'SNR': vfilt_wl_snr, 'CV': vfilt_wl_cv}
	vfpo_dict = {'windows lengths': wl_for_po, 'polyorder': po_array, 'SNR': vfilt_po_snr, 'CV': vfilt_po_cv}

	return vfwl_dict, vfpo_dict

def differential_plot(data_deg, velocity, bins_array, dvsr_for_bins, dvsr_array, bins_for_dvsr):
	# compute snr and cv to velocity
	v_snr = 10 * np.log10(scipy.stats.signaltonoise(velocity))	# compute signal to noise ratio
	v_cv  = scipy.stats.variation(velocity)        				# compute coefficient of variation

	# initialize arrays
	diff_bins 		= []											# initialize array for different bins
	diff_bins_snr 	= []
	diff_bins_cv 	= []

	diff_dvsr 		= []											# initialize array for diferent divisors
	diff_dvsr_snr 	= []
	diff_dvsr_cv 	= []

	# apply differential filter -----------------------------------
	divisor_fixed = dvsr_for_bins
	for bins in bins_array:
		vfb = differentialsmoothing(data_deg, bins, divisor_fixed) 	# filter data with different bins

		vf_snr 	= 10 * np.log10(scipy.stats.signaltonoise(vfb))		# compute signal to noise ratio
		vf_cv 	= scipy.stats.variation(vfb)        				# compute coefficient of variation
		
		diff_bins.append(vfb) 										# add filtered signal to array
		diff_bins_snr.append(vf_snr) 								# add snr
		diff_bins_cv.append(vf_cv) 									# add cv

	bins_fixed = bins_for_dvsr
	for dvsr in dvsr_array:
		vfd = differentialsmoothing(data_deg, bins_fixed, dvsr) 	# filter data with different divisors

		vf_snr 	= 10 * np.log10(scipy.stats.signaltonoise(vfd))		# compute signal to noise ratio
		vf_cv 	= scipy.stats.variation(vfd)        				# compute coefficient of variation

		diff_dvsr.append(vfd)
		diff_dvsr_snr.append(vf_snr) 								# add snr
		diff_dvsr_cv.append(vf_cv) 									# add cv

	# plot --------------------------------------------------------
	f1 = plt.figure(3)
	plt.scatter(np.arange(len(velocity)), velocity, label = 'velocity (deg) SNR={0}dB.CV={1}'.format("%.2f" % v_snr,"%.2f" % v_cv))

	for v_filt, i, snr, cv in itertools.izip(diff_bins,bins_array,diff_bins_snr,diff_bins_cv):
		plt.plot(np.arange(len(v_filt)), v_filt, label = 'bins={0}.SNR={1}dB.CV={2}'.format(i,"%.2f" % snr,"%.2f" % cv))

	plt.legend(loc='upper right')
	plt.title('Velocity filtered by Differential filter. divisor = {0}'.format(divisor_fixed))		
	plt.draw()

	f2 = plt.figure(4)
	plt.scatter(np.arange(len(velocity)), velocity, label = 'velocity (deg) SNR={0}dB.CV={1}'.format("%.2f" % v_snr,"%.2f" % v_cv))

	for v_filt, i, snr, cv in itertools.izip(diff_dvsr,dvsr_array,diff_dvsr_snr,diff_dvsr_cv):
		plt.plot(np.arange(len(v_filt)), v_filt, label = 'dvsr={0}.SNR={1}dB.CV={2}'.format(i,"%.2f" % snr,"%.2f" % cv))
	
	plt.legend(loc='upper right')			
	plt.title('Velocity filtered by Differential filter. bins = {0}'.format(bins_fixed))		
	plt.draw()

	# plt.show()

	# return 
	vfbins_dict = {'bins': bins_array, 'SNR': diff_bins_snr, 'CV': diff_bins_cv}
	vfdvsr_dict = {'divisors': dvsr_array, 'SNR': diff_dvsr_snr, 'CV': diff_dvsr_cv}

	return vfbins_dict, vfdvsr_dict

if __name__ == '__main__':
	main()