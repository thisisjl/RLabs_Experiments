import os, sys

lib_path = os.path.abspath(os.path.join('..','_Libraries'))
sys.path.append(lib_path)

from rlabs_libutils import DataStruct 		# to read data file

import numpy as np
from scipy import signal

import matplotlib.pyplot as plt
import itertools

from Tkinter import Tk 						# for open data file GUI
from tkFileDialog import askopenfilenames 	# for open data file GUI

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
	# apply Savitzky-Golay filter ----------------------------------------------------------------------------------
	vfilt_wl = [] 													# initialize: velocity filtered w/ window lenght
	vfilt_po = [] 													# initialize: velocity filtered w/ polyorder

	# initial parameters
	window_length_array = np.arange(wl_init, number_of_wins, 2)		# compute array of window lengths
	polyorder 	  		= 2 										# poly order must be smaller than window_length
	polyorder_array 	= np.arange(polyorder, number_of_wins)		# compute array of polyorder

	# filter velocity with different window lengths
	for window_length in window_length_array:
		vfilt_wl.append(signal.savgol_filter(velocity, window_length, polyorder))
	
	# filter velocity with different poly orders
	new_window_length_array = []
	for polyorder, idx in itertools.izip(polyorder_array, range(len(polyorder_array))):
		window_length = window_length_array[np.floor(idx/2)]
		if window_length <= polyorder: window_length += 2
		new_window_length_array.append(window_length)
		vfilt_po.append(signal.savgol_filter(velocity, window_length, polyorder))

	# plot --------------------------------------------------------------------------------------------------------------
	f1 = plt.figure(1)
	plt.scatter(np.arange(len(velocity)), velocity, label = 'velocity (deg)')
	for savgol_set, i in itertools.izip(vfilt_wl,window_length_array):
		plt.plot(np.arange(len(savgol_set)), savgol_set, label = 'wl = {0}'.format(i))
	plt.legend(loc='upper right')
	plt.title('Velocity filtered by Savitzky-Golay. Different window lengths. polyorder = 2')		
	plt.draw()

	f2 = plt.figure(2)
	plt.scatter(np.arange(len(velocity)), velocity, label = 'velocity (deg)')
	for savgol_set, i, w in itertools.izip(vfilt_po, polyorder_array, new_window_length_array):
		plt.plot(np.arange(len(savgol_set)), savgol_set, label = 'wl = {0}, po = {1}'.format(w,i))
	plt.legend(loc='upper right')			
	plt.title('Velocity filtered by Savitzky-Golay. Different polyorder'.format())		
	plt.draw()

	# plt.show()

def differential_plot(data_deg, velocity, bins_init, bins_max, dvsr_init, dvsr_max):
	
	# initialize arrays
	diff_bins = [] 													# initialize array for different bins
	diff_dvsr = [] 													# initialize array for diferent divisors

	# initial parameters
	bins_array 	= np.arange(bins_init, bins_max, 1) 				# array of bins number
	dvsr_array	= np.arange(dvsr_init, dvsr_max, 1) 				# array of divisor numbers


	# apply differential filter -----------------------------------
	divisor_fixed = dvsr_init
	for bins in bins_array:
		diff_bins.append(differentialsmoothing(data_deg, bins, divisor_fixed))

	bins_fixed = bins_init
	for dvsr in dvsr_array:
		diff_dvsr.append(differentialsmoothing(data_deg, bins_fixed, dvsr))

	# plot --------------------------------------------------------
	f1 = plt.figure(3)
	plt.scatter(np.arange(len(velocity)), velocity, label = 'velocity (deg)')
	for v_filt, i in itertools.izip(diff_bins,bins_array):
		plt.plot(np.arange(len(v_filt)), v_filt, label = 'bins = {0}'.format(i))
	plt.legend(loc='upper right')
	plt.title('Velocity filtered by Differential filter. divisor = {0}'.format(divisor_fixed))		
	plt.draw()

	f2 = plt.figure(4)
	plt.scatter(np.arange(len(velocity)), velocity, label = 'velocity (deg)')
	for v_filt, i in itertools.izip(diff_dvsr,dvsr_array):
		plt.plot(np.arange(len(v_filt)), v_filt, label = 'dvsr = {0}'.format(i))
	plt.legend(loc='upper right')			
	plt.title('Velocity filtered by Differential filter. bins = {0}'.format(bins_fixed))		
	plt.draw()

	# plt.show()

if __name__ == '__main__':

	# select eyetracker data file
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

	savgol_plot(velocity, wl_init, number_of_wins, po_init) 		# filter velocity


	# Differential filter. -----------------------------------------------------------------------------------------
	# Parameters: bins and divisor.
	# differential_plot() will plot the velocity filtered using different bins and different divisors.
	# For different bins, dvsr_init is used as the fixed divisor.
	# For different divisors, bins_init is used as the fixed bins value.
	# Need to set the initial and maximum values for bins and divisor

	bins_init, bins_max = 2, 10 									# set initial and maximum values for bins
	dvsr_init, dvsr_max	= 2, 10 									# set initial and maximum values for divisor

	differential_plot(data_deg, velocity, 							# filter data
		bins_init, bins_max, dvsr_init, dvsr_max)


	plt.show() 														# show plots