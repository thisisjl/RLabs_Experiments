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

	wl_init 		= 3												# set initial value for window length. must be an odd integer
	po_init 		= 2 											# set initial value for polynomial order
	number_of_wins 	= 10 											# set number of windows

	vfwl_dict, vfpo_dict = savgol_plot(velocity, 					# filter velocity
		wl_init, number_of_wins, po_init) 		


	# Differential filter. -----------------------------------------------------------------------------------------
	# Parameters: bins and divisor.
	# differential_plot() will plot the velocity filtered using different bins and different divisors.
	# For different bins, dvsr_init is used as the fixed divisor.
	# For different divisors, bins_init is used as the fixed bins value.
	# Need to set the initial and maximum values for bins and divisor

	bins_init, bins_max = 2, 10 									# set initial and maximum values for bins
	dvsr_init, dvsr_max	= 2, 10 									# set initial and maximum values for divisor

	vfbins_dict, vfdvsr_dict = differential_plot(data_deg, 			# filter data
		velocity, bins_init, bins_max, dvsr_init, dvsr_max)


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

def savgol_plot(velocity, wl_init, number_of_wins, po_init):
	# apply Savitzky-Golay filter
	vfilt_wl = [] 													# initialize: velocity filtered w/ window length
	vfilt_wl_snr = [] 												# to store snr values of v filtered w/ window length
	vfilt_wl_cv = [] 												# to store cv values of v filtered w/ window length

	vfilt_po = [] 													# initialize: velocity filtered w/ polyorder
	vfilt_po_snr = [] 												# to store snr values of v filtered w/ polyorder
	vfilt_po_cv = [] 												# to store cv values of v filtered w/ polyorder

	# initial parameters
	window_length_array = np.arange(wl_init, number_of_wins, 2)		# compute array of window lengths
	polyorder 	  		= po_init									# poly order must be smaller than window_length
	polyorder_array 	= np.arange(polyorder, number_of_wins)		# compute array of polyorder

	# filter velocity with different window lengths ---------------------------------------------------------------
	for window_length in window_length_array:
		vfwl = signal.savgol_filter(velocity,  						# filter velocity with different window lengths
			window_length, polyorder) 								# vfwl: velocity filtered window length

		vf_snr 	= 10 * np.log10(scipy.stats.signaltonoise(vfwl))	# compute signal to noise ratio
		vf_cv 	= scipy.stats.variation(vfwl)        				# compute coefficient of variation

		vfilt_wl.append(vfwl) 										# add filtered signal to array
		vfilt_wl_snr.append(vf_snr) 								# add snr to array
		vfilt_wl_cv.append(vf_cv) 									# add cv to array
	
	# filter velocity with different poly orders ------------------------------------------------------------------
	new_window_length_array = []
	for polyorder, idx in itertools.izip(polyorder_array, range(len(polyorder_array))):

		window_length = window_length_array[np.floor(idx/2)]
		if window_length <= polyorder: window_length += 2
		new_window_length_array.append(window_length)

		vfpo = signal.savgol_filter(velocity,  						# filter velocity with different polynomial orders
			window_length, polyorder) 								# vfpo: velocity filtered polynomial order
		
		vf_snr 	= 10 * np.log10(scipy.stats.signaltonoise(vfpo))	# compute signal to noise ratio
		vf_cv 	= scipy.stats.variation(vfpo)        				# compute coefficient of variation
		
		vfilt_po.append(vfpo) 										# add filtered signal to array
		vfilt_po_snr.append(vf_snr) 								# add snr
		vfilt_po_cv.append(vf_cv) 									# add cv

	# plot --------------------------------------------------------------------------------------------------------------
	f1 = plt.figure(1)
	plt.scatter(np.arange(len(velocity)), velocity, label = 'velocity (deg)')

	for savgol_set, i, snr, cv in itertools.izip(vfilt_wl,window_length_array, vfilt_wl_snr, vfilt_wl_cv):
		plt.plot(np.arange(len(savgol_set)), savgol_set, label = 'wl={0}.SNR={1}dB.CV={2}'.format(i,"%.2f" % snr,cv))

	plt.legend(loc='upper right')
	plt.title('Velocity filtered by Savitzky-Golay. Different window lengths. polyorder = 2')		
	plt.draw()

	f2 = plt.figure(2)
	plt.scatter(np.arange(len(velocity)), velocity, label = 'velocity (deg)')

	for savgol_set, i, w, snr, cv in itertools.izip(vfilt_po, polyorder_array, new_window_length_array, vfilt_po_snr, vfilt_po_cv):
		plt.plot(np.arange(len(savgol_set)), savgol_set, label = 'wl={0},po={1}.SNR={2}dB.CV={3}'.format(w,i,"%.2f" % snr,cv))

	plt.legend(loc='upper right')			
	plt.title('Velocity filtered by Savitzky-Golay. Different polyorder'.format())		
	plt.draw()

	# plt.show()

	# return 
	vfwl_dict = {'windows lengths': window_length_array, 'polyorder': po_init, 'SNR': vfilt_wl_snr, 'CV': vfilt_wl_cv}
	vfpo_dict = {'windows lengths': new_window_length_array, 'polyorders': polyorder_array, 'SNR': vfilt_po_snr, 'CV': vfilt_po_cv}

	return vfwl_dict, vfpo_dict

def differential_plot(data_deg, velocity, bins_init, bins_max, dvsr_init, dvsr_max):
	
	# initialize arrays
	diff_bins 		= []											# initialize array for different bins
	diff_bins_snr 	= []
	diff_bins_cv 	= []

	diff_dvsr 		= []											# initialize array for diferent divisors
	diff_dvsr_snr 	= []
	diff_dvsr_cv 	= []

	# initial parameters
	bins_array 	= np.arange(bins_init, bins_max, 1) 				# array of bins number
	dvsr_array	= np.arange(dvsr_init, dvsr_max, 1) 				# array of divisor numbers


	# apply differential filter -----------------------------------
	divisor_fixed = dvsr_init
	for bins in bins_array:
		vfb = differentialsmoothing(data_deg, bins, divisor_fixed) 	# filter data with different bins

		vf_snr 	= 10 * np.log10(scipy.stats.signaltonoise(vfb))		# compute signal to noise ratio
		vf_cv 	= scipy.stats.variation(vfb)        				# compute coefficient of variation
		
		diff_bins.append(vfb) 										# add filtered signal to array
		diff_bins_snr.append(vf_snr) 								# add snr
		diff_bins_cv.append(vf_cv) 									# add cv

	bins_fixed = bins_init
	for dvsr in dvsr_array:
		vfd = differentialsmoothing(data_deg, bins_fixed, dvsr) 	# filter data with different divisors

		vf_snr 	= 10 * np.log10(scipy.stats.signaltonoise(vfb))		# compute signal to noise ratio
		vf_cv 	= scipy.stats.variation(vfb)        				# compute coefficient of variation

		diff_dvsr.append(vfd)
		diff_dvsr_snr.append(vf_snr) 								# add snr
		diff_dvsr_cv.append(vf_cv) 									# add cv

	# plot --------------------------------------------------------
	f1 = plt.figure(3)
	plt.scatter(np.arange(len(velocity)), velocity, label = 'velocity (deg)')
	for v_filt, i, snr, cv in itertools.izip(diff_bins,bins_array,diff_bins_snr,diff_bins_cv):
		plt.plot(np.arange(len(v_filt)), v_filt, label = 'bins={0}.SNR={1}dB.CV={2}'.format(i,"%.2f" % snr,cv))
	plt.legend(loc='upper right')
	plt.title('Velocity filtered by Differential filter. divisor = {0}'.format(divisor_fixed))		
	plt.draw()

	f2 = plt.figure(4)
	plt.scatter(np.arange(len(velocity)), velocity, label = 'velocity (deg)')
	for v_filt, i, snr, cv in itertools.izip(diff_dvsr,dvsr_array,diff_dvsr_snr,diff_dvsr_cv):
		plt.plot(np.arange(len(v_filt)), v_filt, label = 'dvsr={0}.SNR={1}dB.CV={2}'.format(i,"%.2f" % snr,cv))
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