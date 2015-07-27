import os, sys
lib_path = os.path.abspath(os.path.join('..','_Libraries'))
sys.path.append(lib_path)
from rlabs_libutils import DataStruct, select_data, gentimeseries, gencontinuousoutliers, filteroutliers, timestampsfromcontinouosoutliers, uniquelist_withidx
import pandas as pd
import matplotlib.pyplot as plt
from itertools import izip
import numpy as np

def main(outlier_threshold = 125, ambiguousoutlier_th = 100, filter_samples = 5, a_color = 'gray',	b_color = 'lightgray'):
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

	# get eytracker's time stamps for outliers
	A_eye_percept_ts = timestampsfromcontinouosoutliers(df['A percept continuous'], df['time'])
	B_eye_percept_ts = timestampsfromcontinouosoutliers(df['B percept continuous'], df['time'])

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

	# # --------------------------------------------------------------------------------------------
	# # figure 1: a) gaze position with reported and extracted percepts
	# #			  b) outliers vs no-outliers with reported and extracted percepts
	f3, ax3 = plt.subplots(2, sharex = True)

	ax3[0].plot(df['time'], df['LEpos_int'], label = 'leftgazeX (interpolated)') 												# velocity
	ax3[0].set_title('Position trace (degrees)')

	ax3[1].scatter(notevenambg_outliers['time'], notevenambg_outliers['velocity'], color = 'g', label='non-outliers') 			# non-outliers
	ax3[1].scatter(ambg_outliers['time'], ambg_outliers['velocity'], color = 'b', label='ambg_outliers') 						# ambiguous outliers
	ax3[1].scatter(outliers['time'], outliers['velocity'], color = 'r', label='outliers') 										# outliers
	for event in ds.trial_ts:
		ax3[1].plot((event, event), (np.min(outliers['velocity']),np.max(outliers['velocity'])), 'k-') 							# vertical line for trials
	ax3[1].set_title('Velocity with outliers. 1st_th={0} 2nd_th2={1}'.format(outlier_threshold,ambiguousoutlier_th))
	ax3[1].legend()

	for i in range(2):
		for event in ds.trial_ts:
			ax3[i].plot((event, event), (np.min(df['LEpos_int']),np.max(df['LEpos_int'])), 'k-')								# line to indicate start and end of trial
		for on, off in ds.A_ts:
			ax3[i].axvspan(on, off, ymin=0.5, ymax=1, facecolor=a_color, linewidth=0, alpha=0.5, label = 'A percept') 			# reported percepts for a (button press)
		for on, off in ds.B_ts:
			ax3[i].axvspan(on, off, ymin=0.5, ymax=1, facecolor=b_color, linewidth=0, alpha=0.5, label = 'B percept') 			# reported percepts for b

		for j in range(len(A_eye_percept_ts)/2-1):
			on  = A_eye_percept_ts[2*j]
			off = A_eye_percept_ts[2*j+1]
			ax3[i].axvspan(on, off, ymin=0, ymax=.5, facecolor=a_color, linewidth=0, alpha=0.5) 								# extracted percepts for a 
		for j in range(len(B_eye_percept_ts)/2-1):
			on  = B_eye_percept_ts[2*j]
			off = B_eye_percept_ts[2*j+1]
			ax3[i].axvspan(on, off, ymin=0, ymax=.5, facecolor=b_color, linewidth=0, alpha=0.5)									# extracted percepts for b

		ax3[i].set_ylabel("Extracted percepts | Reported percepts")

	# Get artists and labels for legend of first subplot
	handles, labels = ax3[0].get_legend_handles_labels()
	labelsidx, labels = uniquelist_withidx(labels)
	ax3[0].legend([handles[idx] for idx in labelsidx], labels)

	ax3[1].set_xlabel('time (ms)')

	f3.suptitle(fn)

	# # # --------------------------------------------------------------------------------------------
	# # # figure 2: a) gaze position, b) outliers vs no-outliers,	c) filtered outliers vs no-outliers
	# f2, ax2 = plt.subplots(3, sharex = True)

	# ax2[0].plot(df['time'], df['LEpos_int'], label = 'leftgazeX (interpolated)')
	# for event in ds.trial_ts:
	# 	ax2[0].plot((event, event), (np.min(df['LEpos_int']),np.max(df['LEpos_int'])), 'k-')
	# ax2[0].set_title('Position trace (degrees)')
	# ax2[0].legend()

	# ax2[1].scatter(notevenambg_outliers['time'], notevenambg_outliers['velocity'], color = 'g', label='non-outliers')
	# ax2[1].scatter(ambg_outliers['time'], ambg_outliers['velocity'], color = 'b', label='ambg_outliers')
	# ax2[1].scatter(outliers['time'], outliers['velocity'], color = 'r', label='outliers')
	# for event in ds.trial_ts:
	# 	ax2[1].plot((event, event), (np.min(outliers['velocity']),np.max(outliers['velocity'])), 'k-')
	# ax2[1].set_title('Velocity with outliers. 1st_th={0} 2nd_th2={1}'.format(outlier_threshold,ambiguousoutlier_th))
	# ax2[1].legend()

	# ax2[2].scatter(filtnonoutliers['time'], filtnonoutliers['velocity'], color = 'g', label='filt-non-outliers')
	# ax2[2].scatter(filtoutliers['time'], filtoutliers['velocity'], color = 'r', label='filt-outliers')
	# for event in ds.trial_ts:
	# 	ax2[2].plot((event, event), (np.min(filtnonoutliers['velocity']),np.max(filtnonoutliers['velocity'])), 'k-')
	# ax2[2].set_title('Velocity with outliers. th1:{0} filter samples:{1}'.format(outlier_threshold, filter_samples))
	# ax2[2].legend()
	
	# ax2[2].set_xlabel('time (ms)')
	# f2.suptitle(fn)

	plt.show()


if __name__ == '__main__':
	main()