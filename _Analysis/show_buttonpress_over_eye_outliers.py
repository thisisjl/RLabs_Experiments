import os, sys
lib_path = os.path.abspath(os.path.join('..','_Libraries'))
sys.path.append(lib_path)
from rlabs_libutils import DataStruct, select_data, gentimeseries, gencontinuousoutliers, filteroutliers
import pandas as pd
import matplotlib.pyplot as plt
from itertools import izip
import numpy as np

def main(outlier_threshold = 125, ambiguousoutlier_th = 100, filter_samples = 5):
	# define convert-to-degrees constants
	pix = 1280
	DPP = 0.03
	framerate = 120.0

	# select data
	path = select_data()
	print path

	# get raw data
	ds = DataStruct(path)
	fn = ds.filename.split()[0] # get filename

	time = pd.Series(ds.timestamps)
	leftgazeX = pd.Series(ds.leftgazeX)
	df = pd.DataFrame({'time': time, 'LEpos': leftgazeX})

	# get rid of -1.1 (NaN's)
	mask = df['LEpos'] == -1.1
	df['LEpos'].loc[mask] = None

	# convert LEpos to degs
	df['LEpos'] = df['LEpos'] * pix * DPP

	# interpolate eye position
	df['LEpos_int'] = df['LEpos'].interpolate()

	# compute velocity for interpolated position:
	df['velocity'] = df['LEpos_int'].diff() * framerate

	# compute outliers (boolean array):
	df['isOutlier'] = abs(df['velocity'] - df['velocity'].mean()) > outlier_threshold

	# create two new DataFrames: for outliers and non-outliers:
	outliers = df[df['isOutlier']].dropna()
	nonoutliers = df[~df['isOutlier']].dropna()

	# compute ambiguous outliers
	df['isAmbiguousOutlier'] = (abs(df['velocity'] - df['velocity'].mean()) > ambiguousoutlier_th) & (~df['isOutlier'])

	# create two new DataFrames: for ambiguous-outliers and non-outliers:
	ambg_outliers = df[df['isAmbiguousOutlier']].dropna()
	notevenambg_outliers = df[~df['isAmbiguousOutlier']].dropna()

	# compute A or B given outliers
	df['A percept'] = [v>0 if o else 0 for v,o in izip(df['velocity'],df['isOutlier'])]
	df['B percept'] = [v<0 if o else 0 for v,o in izip(df['velocity'],df['isOutlier'])]

	# compute continuous A or B percepts
	df['A percept continuous'] = gencontinuousoutliers(df['A percept'],df['B percept'])
	df['B percept continuous'] = gencontinuousoutliers(df['B percept'],df['A percept'])

	# filter outliers
	# 	so outliers will only be valid if are separated from previous outliers
	# 	by a X time distance.
	# 	compute time:
	# mintime = 0.3 			# seconds
	# samples = framerate * mintime
	df['Outlierfiltered'] = filteroutliers(df['isOutlier'], samples = filter_samples)

	# create two new DataFrames: for filtered outliers and filtered non-outliers:
	filtoutliers = df[df['Outlierfiltered']].dropna()
	filtnonoutliers = df[~df['Outlierfiltered']].dropna()

	# generate percept time series (button presses)
	df['A press'] = gentimeseries(ds.timestamps, ds.A_ts)
	df['B press'] = gentimeseries(ds.timestamps, ds.B_ts)

	# # plots --------------------------------------------------------------------------------
	# # figure 1: 4 subplots with a) gaze position, b) outliers vs no-outliers, 
	# # 			c) button presses vs eye outliers (for A percept)
	# # 			d) button presses vs eye outliers (for B percept)
	f1, ax1 = plt.subplots(4, sharex = True)
	ax1[0].plot(df['time'], df['LEpos_int'], label = 'leftgazeX (interpolated)')
	for event in ds.trial_ts:															# for each event time stamp
		ax1[0].plot((event, event), (np.min(df['LEpos_int']),np.max(df['LEpos_int'])), 'k-')
	ax1[0].set_title('Position trace')
	ax1[0].legend()

	ax1[1].scatter(nonoutliers['time'], nonoutliers['velocity'], color ='g', label='non-outliers') 
	ax1[1].scatter(outliers['time'], outliers['velocity'], color = 'r', label='outliers')
	for event in ds.trial_ts:
		ax1[1].plot((event, event), (np.min(outliers['velocity']),np.max(outliers['velocity'])), 'k-')
	ax1[1].set_title('Velocity with outliers. th:{0}'.format(outlier_threshold))
	ax1[1].set_ylim()
	ax1[1].legend()

	ax1[2].plot(df['time'], df['A press'], color = 'r',linewidth=2, label = 'A button press')
	ax1[2].plot(df['time'], df['A percept continuous'], color = 'lightsalmon',linewidth=1, label = 'A eye outlier')
	for event in ds.trial_ts:
		ax1[2].plot((event, event), (np.min(df['A press'])-0.05,np.max(df['A press'])+0.05), 'k-')
	ax1[2].set_title('A percept: buttons vs eye outliers')
	ax1[2].set_ylim([0, 1.05])
	ax1[2].legend()

	ax1[3].plot(df['time'], df['B press'], color = 'b',linewidth=2, label = 'B button press')
	ax1[3].plot(df['time'], df['B percept continuous'], color = 'lightblue',linewidth=1, label = 'B eye outlier')
	for event in ds.trial_ts:
		ax1[3].plot((event, event), (np.min(df['B press'])-0.05,np.max(df['B press'])+0.05), 'k-')
	ax1[3].set_title('B percept: buttons vs eye outliers')
	ax1[3].set_ylim([0, 1.05])
	ax1[3].legend()

	ax1[3].set_xlabel('time (ms)')
	f1.suptitle(fn)

	# # --------------------------------------------------------------------------------------------
	# # figure 2: 4 subplots with a) gaze position, 
	# #							b) outliers vs no-outliers,
	# # 							c) filtered outliers vs no-outliers
	f2, ax2 = plt.subplots(3, sharex = True)

	ax2[0].plot(df['time'], df['LEpos_int'], label = 'leftgazeX (interpolated)')
	for event in ds.trial_ts:
		ax2[0].plot((event, event), (np.min(df['LEpos_int']),np.max(df['LEpos_int'])), 'k-')
	ax2[0].set_title('Position trace in degrees')
	ax2[0].legend()

	ax2[1].scatter(notevenambg_outliers['time'], notevenambg_outliers['velocity'], color = 'g', label='non-outliers')
	ax2[1].scatter(ambg_outliers['time'], ambg_outliers['velocity'], color = 'b', label='ambg_outliers')
	ax2[1].scatter(outliers['time'], outliers['velocity'], color = 'r', label='outliers')
	for event in ds.trial_ts:
		ax2[1].plot((event, event), (np.min(outliers['velocity']),np.max(outliers['velocity'])), 'k-')
	ax2[1].set_title('Velocity with outliers determined 1.96 * SD')
	ax2[1].legend()

	ax2[2].scatter(filtnonoutliers['time'], filtnonoutliers['velocity'], color = 'g', label='filt-non-outliers')
	ax2[2].scatter(filtoutliers['time'], filtoutliers['velocity'], color = 'r', label='filt-outliers')
	for event in ds.trial_ts:
		ax2[2].plot((event, event), (np.min(filtnonoutliers['velocity']),np.max(filtnonoutliers['velocity'])), 'k-')
	ax2[2].set_title('Velocity with filtered outliers determined 1.96 * SD')
	ax2[2].legend()
	
	ax2[2].set_xlabel('time (ms)')
	f2.suptitle(fn)
	

	plt.show()


if __name__ == '__main__':
	main()