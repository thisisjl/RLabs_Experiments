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
	# path = os.path.join('SampleData', 'Randomdots-15.05.13_16.52_EB2_Rdots_eyetracker_data.txt')
	# path = os.path.join('SampleData', 'Randomdots-15.05.13_16.54_JL2_Rdots_eyetracker_data.txt')
	path = os.path.join('SampleData', 'Randomdots-15.05.13_16.53_JL_Rdots_eyetracker_data.txt')
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
	# vel  = pd.Series(np.diff(df["LEpos"],  n=1) * framerate);  # DON'T USE NP.DIFF - CALC Wrong - http://stackoverflow.com/questions/13689512/numpy-diff-on-a-pandas-series
	
	vel = df.LEpos.diff() * framerate
	t = df.time[1:]
	dfVel = pd.DataFrame({"time": t, "LEvel": vel})

	# VELOCITY from INTERPOLATED POSITION TRACE
	vel_int = df_int.LEpos.diff() * framerate
	t_int = df_int.time[1:]
	dfVel_int = pd.DataFrame({"time": t_int, "LEvel": vel_int})

	# Calculate Outliers -------------------------------------------------------------------------------------

	# Velocity without interpolation
	dfVel['Outlier'] = abs(dfVel['LEvel'] - dfVel['LEvel'].mean()) > 1.96*dfVel['LEvel'].std()
	dfVel['x-Mean'] = abs(dfVel['LEvel'] - dfVel['LEvel'].mean())
	dfVel['1.96*sd'] = 1.96*(dfVel['LEvel'].std())

	cond = dfVel.Outlier == True 						# index based on whether outlier or not
	vel_subset_a = dfVel[cond].dropna()
	vel_subset_b = dfVel[~cond].dropna()

	# Velocity with interpolation
	dfVel_int['Outlier'] = abs(dfVel_int['LEvel'] - dfVel_int['LEvel'].mean()) > 1.96*dfVel_int['LEvel'].std()
	dfVel_int['x-Mean'] = abs(dfVel_int['LEvel'] - dfVel_int['LEvel'].mean())
	dfVel_int['1.96*sd'] = 1.96*(dfVel_int['LEvel'].std())

	cond_int = dfVel_int.Outlier == True				# index based on whether outlier or not
	vel_subset_a_int = dfVel_int[cond_int].dropna()
	vel_subset_b_int = dfVel_int[~cond_int].dropna()

	# Plotting -----------------------------------------------------------------------------------------------

	f, ax = plt.subplots(3, 2, sharex = True, figsize = (20,10))

	# # FIG 2, subplot 1
	ax[0,0].scatter(df.time, df.LEpos, color = 'r')
	ax[0,0].set_title('Position trace in degrees')

	# # FIG 2, subplot 2
	ax[0,1].scatter(df_int.time, df_int.LEpos, color = 'r')
	ax[0,1].set_title('Interpolated position trace in degrees')

	# # FIG 2, subplot 3
	ax[1,0].scatter(dfVel.time, dfVel.LEvel, color = 'g')
	ax[1,0].plot(dfVel.time, dfVel.LEvel)
	ax[1,0].set_title('Velocity trace (deg/s) using Pandas differentiation')

	# # FIG 2, subplot 4
	ax[1,1].scatter(dfVel_int.time, dfVel_int.LEvel, color = 'g')
	ax[1,1].plot(dfVel_int.time, dfVel_int.LEvel)
	ax[1,1].set_title('Interpolated velocity trace (deg/s) using Pandas differentiation')

	# FIG 2, subplot 5
	ax[2,0].scatter(vel_subset_a.time, vel_subset_a.LEvel, color = 'r', label='outliers')
	ax[2,0].scatter(vel_subset_b.time, vel_subset_b.LEvel, color ='g', label='non-outliers') 
	ax[2,0].set_title('Velocity with outliers determined 1.96 * SD')
	ax[2,0].legend()

	# FIG 2, subplot 6
	ax[2,1].scatter(vel_subset_a_int.time, vel_subset_a_int.LEvel, color = 'r', label='outliers')
	ax[2,1].scatter(vel_subset_b_int.time, vel_subset_b_int.LEvel, color ='g', label='non-outliers') 
	ax[2,1].set_title('Interpolated velocity with outliers determined 1.96 * SD')
	ax[2,1].legend()

	plt.show()


if __name__ == '__main__':
	main()