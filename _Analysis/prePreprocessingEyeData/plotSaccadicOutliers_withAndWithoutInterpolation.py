import os, sys

lib_path = os.path.abspath(os.path.join('../..','_Libraries'))
sys.path.append(lib_path)

from rlabs_libutils import DataStruct, movingaverage, select_data
# from selectData_lib import *

import numpy as np
import pandas as pd
from scipy import signal
import scipy.stats

import matplotlib.pyplot as plt
import itertools

import math

# from Tkinter import Tk 						# for open data file GUI
# from tkFileDialog import askopenfilenames 	# for open data file GUI

# from itertools import count 				# create counter for figures
# figcount = count()

def main():

	# define constants --------------------------------------------------------------------------------------------
	pix = 1280
	DPP = 0.03
	framerate = 120.0

	# read data ---------------------------------------------------------------------------------------------------
	# path = os.path.join('SampleData', 'Plaid_v19-15.03.09_17.26_EB1_newdata_eyet.txt') 	# read data
	path = os.path.join('SampleData', 'Randomdots-15.05.13_16.52_EB2_Rdots_eyetracker_data.txt')
	# path = os.path.join('SampleData', 'Randomdots-15.05.13_16.54_JL2_Rdots_eyetracker_data.txt')
	# path = os.path.join('SampleData', 'Randomdots-15.05.13_16.53_JL_Rdots_eyetracker_data.txt')
	# path = os.path.join('SampleData', 'Plaid-15.03.25_16.19_JL_fixplusprotectionzone_eyetracker_data.txt')

	ds = DataStruct(path)
	time = pd.Series(ds.timestamps)
	leftgazeX = pd.Series(ds.leftgazeX)
	df = pd.DataFrame({'time': time, 'LEpos': leftgazeX})

	# remove NaN's -------------------------------------------------------------------------------------------
	mask = df['LEpos'] == -1.1
	df.loc[mask] = None

	# convert to degrees -------------------------------------------------------------------------------------------
	
	df["LEpos"]= df["LEpos"] * pix					# convert from arbitrary units to pixels
	df["LEpos"]= df["LEpos"] * DPP				# convert from pixels to degrees

	# Interpolate --------------------------------------------------------------------------------------------
	df_int = df.interpolate()

	# Calculate velocity -------------------------------------------------------------------------------------

	# VELOCITY from RAW POSITION TRACE 
	dfVel = calcVel(df.time, df.LEpos, framerate) 			# three arguments: (1) time vector from dataframe, 
															# (2) position vector from dataframe (3) framerate	 

	# VELOCITY from INTERPOLATED POSITION TRACE
	dfVel_int = calcVel(df_int.time, df_int.LEpos, framerate) 	# three arguments: (1) time vector from dataframe, 
																# (2) position vector from dataframe (3) framerate	


	# Calculate Outliers -------------------------------------------------------------------------------------

	# Velocity without interpolation
	dfVel, vel_subset_a, vel_subset_b = calcOutl(dfVel, dfVel.LEvel)

	# Velocity with interpolation
	dfVel_int, vel_subset_a_int, vel_subset_b_int = calcOutl(dfVel_int, dfVel_int.LEvel)


	# Hayashi filter -----------------------------------------------------------------------------------------

	smooth_vel, sign_vel_avg, vel_avg, sign_vel, num2_samples, num_samples = hayashi(dfVel_int.LEvel, framerate, avg_win1 = 0.3, avg_win2 = 0.5, val1 = 30, val2 = 0.1)
	start1 = math.ceil(num_samples/2.) - 1 # because index starts at 0 and not 1
	end1 = start1 + len(vel_avg)
	time_start = start1 + math.ceil(num2_samples/2.) - 1 # because index starts at 0 and not 1
	time_end = time_start + len(smooth_vel)

	# Plotting -----------------------------------------------------------------------------------------------

	# FIGURE 1 - Effect of interpolation on detection of outliers
	f, ax = plt.subplots(3, 2, sharex = True, figsize = (20,10))

	# # FIG 1, subplot 1
	ax[0,0].scatter(df.time, df.LEpos, color = 'r')
	ax[0,0].set_title('Position trace in degrees')

	# # FIG 1, subplot 2
	ax[0,1].scatter(df_int.time, df_int.LEpos, color = 'r')
	ax[0,1].set_title('Interpolated position trace in degrees')

	# # FIG 1, subplot 3
	ax[1,0].scatter(dfVel.time, dfVel.LEvel, color = 'g')
	ax[1,0].plot(dfVel.time, dfVel.LEvel)
	ax[1,0].set_title('Velocity trace (deg/s) using Pandas differentiation')

	# # FIG 1, subplot 4
	ax[1,1].scatter(dfVel_int.time, dfVel_int.LEvel, color = 'g')
	ax[1,1].plot(dfVel_int.time, dfVel_int.LEvel)
	ax[1,1].set_title('Interpolated velocity trace (deg/s) using Pandas differentiation')

	# FIG 1, subplot 5
	ax[2,0].scatter(vel_subset_a.time, vel_subset_a.LEvel, color = 'r', label='outliers')
	ax[2,0].scatter(vel_subset_b.time, vel_subset_b.LEvel, color ='g', label='non-outliers') 
	ax[2,0].set_title('Velocity with outliers determined 1.96 * SD')
	ax[2,0].legend()

	# FIG 1, subplot 6
	ax[2,1].scatter(vel_subset_a_int.time, vel_subset_a_int.LEvel, color = 'r', label='outliers')
	ax[2,1].scatter(vel_subset_b_int.time, vel_subset_b_int.LEvel, color ='g', label='non-outliers') 
	ax[2,1].set_title('Interpolated velocity with outliers determined 1.96 * SD')
	ax[2,1].legend()



	# FIGURE 2 - comparison of Hayashi filter to interpolated outlier method
	f2, ax2 = plt.subplots(3, 2, sharex = True, figsize = (20,10))

	# # FIG 2, subplot 1
	ax2[0,0].scatter(df_int.time, df_int.LEpos, color = 'r')
	ax2[0,0].set_title('Interpolated position trace in degrees')

	# # FIG 2, subplot 3
	ax2[1,0].scatter(dfVel_int.time, dfVel_int.LEvel, color = 'g')
	ax2[1,0].plot(dfVel_int.time, dfVel_int.LEvel)
	ax2[1,0].set_title('Interpolated velocity trace (deg/s) using Pandas differentiation')

	# FIG 2, subplot 5
	ax2[2,0].scatter(vel_subset_a_int.time, vel_subset_a_int.LEvel, color = 'r', label='outliers')
	ax2[2,0].scatter(vel_subset_b_int.time, vel_subset_b_int.LEvel, color ='g', label='non-outliers') 
	ax2[2,0].set_title('Interpolated velocity with outliers determined 1.96 * SD')
	ax2[2,0].legend()

	# FIG 2, subplot 2
	ax2[0,1].scatter(df_int.time, df_int.LEpos, color = 'r')
	ax2[0,1].set_title('Interpolated position trace in degrees (same as subplot 1)')

	# FIG 2, subplot 4
	# ax2[1,1].scatter(df_int.time, sign_vel, color = 'g')
	# ax2[1,1].set_title('Step 1: calculated sign of interpolated velocity for Hayashi filter')
	ax2[1,1].scatter(dfVel_int.time[int(start1):int(end1)], vel_avg, color = 'g')
	ax2[1,1].set_title('Smoothed output after first averaging window from Hayashi')

	# FIG 2, subplot 6
	ax2[2,1].scatter(dfVel_int.time[int(time_start):int(time_end)], smooth_vel, color = 'g')
	ax2[2,1].set_title('Smoothed output after 2nd avg win from Hayashi filter')



	# FIG 3 - for printing
	f3, ax3 = plt.subplots(2, 1, sharex = True, figsize = (20,10))

	# # FIG 3, subplot 1
	ax3[0].scatter(df_int.time, df_int.LEpos, color = 'r')
	ax3[0].set_title('Interpolated position trace in degrees')

	# FIG 2, subplot 2
	ax3[1].scatter(vel_subset_a_int.time, vel_subset_a_int.LEvel, color = 'r', label='outliers')
	ax3[1].scatter(vel_subset_b_int.time, vel_subset_b_int.LEvel, color ='g', label='non-outliers') 
	ax3[1].set_title('Interpolated velocity with outliers determined 1.96 * SD')
	ax3[1].legend()
	fname = 'rawdata_outliers.pdf'
	plt.savefig(fname)

	plt.show()

def calcVel(dft, dfp, fr):

	# vel  = pd.Series(np.diff(df.LEpos,  n=1) * framerate);  # DON'T USE NP.DIFF - CALC Wrong - http://stackoverflow.com/questions/13689512/numpy-diff-on-a-pandas-series
	vel = dfp.diff() * fr
	t = dft[1:]
	dfVel = pd.DataFrame({"time": t, "LEvel": vel})
	return dfVel

def calcOutl(df, dfv):

	df['Outlier'] = abs(dfv - dfv.mean()) > 1.96*dfv.std()
	df['x-Mean'] = abs(dfv - dfv.mean())
	df['1.96*sd'] = 1.96*(dfv.std())

	cond = df.Outlier == True 						# index based on whether outlier or not
	vel_subset_a = df[cond].dropna()
	vel_subset_b = df[~cond].dropna()
	return df, vel_subset_a, vel_subset_b

def hayashi(velocity, fr, avg_win1 = 0.3, avg_win2 = 1, val1 = 50, val2 = 0.1):
	
	# make sure avg sample is odd because then the smooth series will be "in phase" with the original series

	num_samples 	= fr * avg_win1 - 1		# Hayashi uses 300 ms time window; subtract 1 to get an odd # of samples
	num2_samples	= fr * avg_win2	- 1		# Hayashi uses 1000 ms time window

	# (1) "calculate sign of eye velocity": 
	sign_vel = calculateSign(velocity, val1)  # ignore any velocity values less than abs(50 deg/s) 


	# (2) calculate sign of the moving average of sign_vel
	# (within a 300-ms time window) 
	vel_avg = movingaverage(sign_vel, num_samples)
	sign_vel_avg = calculateSign(vel_avg, val2)


	# (3) smooth the output using a 1-s time window
	smooth_vel = movingaverage(sign_vel_avg, num2_samples)


	# (4) Calculate cross-correlation between button press reports 
	# and the filtered velocity data to estimate optimal time shift

	# (5) Filter output to [1, 0, -1] under the threshold of +/- 0.5
	# to reproduce the button presss reports on perception

	# (6) Calculate the matching index - the % of the number of time
	# points within which the filtered output matches the actual button
	# press reports if the filtered output was non-zero
	
	return smooth_vel, sign_vel_avg, vel_avg, sign_vel, num2_samples, num_samples

def calculateSign(dfv, val):
    df = pd.DataFrame({"LEvel": dfv})
    df['Signal'] = np.nan
    
    df.ix[df.LEvel < -val, "Signal"] = -1
    df.ix[df.LEvel > val, "Signal"] = 1 
    df.ix[(df.LEvel < val) & (df.LEvel > - val), "Signal"] = 0
    return df.Signal

	# signal 		= []
	# for value in array:
	# 	if value < 0:
	# 		signal.append(-1)
	# 	if value > 0:
	# 		signal.append(1)
	# 	if value == 0:
	# 		signal.append(0)
	# return signal

if __name__ == '__main__':
	main()