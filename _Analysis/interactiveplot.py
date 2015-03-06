import glob 							# to list the files in directory
import sys								# to parse input
import numpy as np 						# to read data
import matplotlib.pyplot as plt 		# to plot
import os 								# to save figures in folder
import time 							# to name figures

from collections import OrderedDict		# for plotTC

from Tkinter import Tk 						# for open file GUI
from tkFileDialog import askopenfilenames 	# for open file GUI
from tkSimpleDialog import askstring
from tkMessageBox import askquestion

# import mpld3							# to save figures to html with zoom

from bokeh.resources import CDN
from bokeh.embed import components, file_html
from bokeh import mpl
from bokeh.plotting import figure, output_file, show, VBox

# DIR_IN='exp_sets/'
# DIR_OUT='Tvsf_res_files/'
# fWeb_NAME='Tvsf_res'
# fWeb_HEADER='Tvsf_html_header_SAV.txt'
# DATE_TIME_format='yyyy-mm-dd_HHMM'
outformat = 'png'
ithtml = 'interactivehtml.html' 

create_ihtml = 0
create_ihtml_bokeh = 1

import shutil # to delete folders
import time # to wait for gif creation

def main(datafileslist = '', DIR_IN='', DIR_OUT='', fWebName='', fWeb_HEADER='html_template.html', DATE_TIME_format="%Y-%m-%d_%H.%M", input_extension = '*.txt',
	left_rgb = (1.0, 0., 0.), right_rgb = (0., 1.0, 0.), YvalsA=[0.80, 0.90, 0, 1], YvalsB=[0.75, 0.85, 0, 1],
	apply_fade = 1, fade_sec = 0.5, samplingfreq = 120.0, shiftval = 0.05, color_shift = [-0.3,0,0], plotrange = [-0.1,1.1], forshow0_forsave1 = 0,
	createvideoYN = 0, create_highangle_videoYN = 0, videofortrials = (0,-1)):

	ihtml_figs = []
	###########################################					
	# Scale Yvals to plotrange
	###########################################		
	YvalsA = np.array(YvalsA) * plotrange[1]
	YvalsB = np.array(YvalsB) * plotrange[1]


	###############################################
	# From the list of datafiles, read data,
	# create plots and save them in DIR_OUT as jpgs
	###############################################
	for datafile in datafileslist:											# for each data file
		print 'datafile used: {0}\n'.format(os.path.split(datafile)[1])		# print the name of the current data file 

		ds = DataStruct()													# create new DataStruct instance
		ds = read_data2(ds, datafile)										# read data and store in datastruct

		if create_ihtml_bokeh: mb_container = my_bokeh_html_container()

		# container = [{'script':'', 'div':'', 'video':''} for k in range(ds.numtrials + 2)]

		mycontainer = [html_container() for k in range(ds.numtrials + 2)] 
		cit = 0 	# container iterator

		Tmax = ds.trial_ts[-1] + 3000										# get ending time of last trial
	
		if create_ihtml_bokeh and 0:

			###########################################
			# Create plot: two subplots with input
			###########################################
	
			bokehfig = figure(title = 'Input time stamps')
			plot = bokeh_plotTC(bokehfig, ds.left_ts, Tmax, YvalsA, left_rgb, change_axis=1, label = 'Left input')		# plot TC. left press
			plot = bokeh_plotTC(bokehfig, ds.right_ts, Tmax, YvalsB, right_rgb, change_axis=1, label = 'Right input')	# plot TC. left press
			
			bokehfig.xaxis.axis_label='Time (ms)'

			mb_container.append(components(plot, CDN)) # components returns the variables 'script' and 'div' that contain a javascript/html string for bokehfig


		##########################################################
		# Plot all the trials. X and Y coordinate over time stamps
		##########################################################

		if create_ihtml_bokeh:

			## plot X coordinate for both eyes

			bokehfig = figure(title = 'X coordinates. Right eye shifted {0}'.format(shiftval))
			bokeh_plot_gaze(bokehfig, ds.timestamps, ds.leftgazeX, ds.rightgazeX, trial_ts = ds.trial_ts, label1 = 'left eye', label2 = 'right eye', 
			X_color = left_rgb, Y_color = right_rgb, shiftval = shiftval, plotrange = plotrange)

			plot = bokeh_plotTC(bokehfig, ds.left_ts, Tmax, YvalsA, left_rgb, change_axis=1, label = 'Left input')		# plot TC. left press
			plot = bokeh_plotTC(bokehfig, ds.right_ts, Tmax, YvalsB, right_rgb, change_axis=1, label = 'Right input')		# plot TC. left press
			
			bokehfig.xaxis.axis_label='Time (ms)'
			bokehfig.yaxis.axis_label='X gaze'

			# samples = 5
			# LGavg = movingaverage(ds.leftgazeX[idx_start:idx_end], samples)
			# TSavg = movingaverage(ds.timestamps[idx_start:idx_end], samples)
			# # print LGavg

			# bokehfig.line(TSavg, LGavg, size=12, color="red", alpha=0.5)

			# script, div = components(plot, CDN)
			mb_container.append(components(plot, CDN))
			mycontainer[cit].scriptX, mycontainer[cit].divX = components(plot, CDN)
			# container[cit]['script'], container[cit]['div'], = components(plot, CDN)
			# cit += 1

			## plot Y coordinate for both eyes

			bokehfig = figure(title = 'Y coordinates. Right eye shifted {0}'.format(shiftval))
			bokeh_plot_gaze(bokehfig, ds.timestamps, ds.leftgazeY, ds.rightgazeY, trial_ts = ds.trial_ts, label1 = 'left eye', label2 = 'right eye', 
			X_color = left_rgb, Y_color = right_rgb, shiftval = shiftval, plotrange = plotrange)

			plot = bokeh_plotTC(bokehfig, ds.left_ts, Tmax, YvalsA, left_rgb, change_axis=1, label = 'Left input')		# plot TC. left press
			plot = bokeh_plotTC(bokehfig, ds.right_ts, Tmax, YvalsB, right_rgb, change_axis=1, label = 'Right input')		# plot TC. left press
			
			bokehfig.xaxis.axis_label='Time (ms)'
			bokehfig.yaxis.axis_label='Y gaze'


			mb_container.append(components(plot, CDN))
			mycontainer[cit].scriptY, mycontainer[cit].divY = components(plot, CDN)
			cit += 1


			if createvideoYN and 0: createmp4(ds.timestamps, ds.leftgazeX, ds.leftgazeY, videoname = 'alltrials.mp4')


		if create_ihtml_bokeh and ds.numtrials > 1:
			######################################
			# For each trial, plot gaze and input
			######################################
			it = 0																# iterator
			for trial in range(ds.numtrials):
				## Compute indexes. TrialEvent times do not have to match eyetracker times

				if apply_fade: fade_samp = samplingfreq * fade_sec				# obtain samples for data fade
				
				start = ds.trial_ts[it]											# start of trial value
				end = ds.trial_ts[it+1]											# end of trial value

				val, idx_start = find_nearest_above(ds.timestamps, start)		# find nearest above eyetracker time stamp

				if apply_fade and not trial == 0: 								# for the first trial, there's no fade in.
					idx_start = idx_start - fade_samp 							# apply fade in

				if not trial == (ds.numtrials-1):								# if not the last trial,
					val, idx_end = find_nearest_above(ds.timestamps, end)		# find nearest above eyetracker time stamp

					if apply_fade: idx_end = idx_end + fade_samp				# apply fade out
				else:
					idx_end = end


				trial_ts = [start, end]

				## plot X coordinate for both eyes

				bokehfig = figure(title = 'Trial {0}. X coordinate. Right eye shifted {1}'.format(trial+1,shiftval))
				bokeh_plot_gaze(bokehfig, ds.timestamps[idx_start:idx_end], ds.leftgazeX[idx_start:idx_end], ds.rightgazeX[idx_start:idx_end], 
					trial_ts = trial_ts, label1 = 'left eye', label2 = 'right eye', X_color = left_rgb, Y_color = right_rgb, shiftval = shiftval, plotrange = plotrange)

				plot = bokeh_plotTC(bokehfig, ds.left_trial[trial], Tmax, YvalsA, left_rgb, change_axis=1, label = 'Left input')		# plot TC. left press
				plot = bokeh_plotTC(bokehfig, ds.right_trial[trial], Tmax, YvalsB, right_rgb, change_axis=1, label = 'Right input')		# plot TC. left press
				
				bokehfig.xaxis.axis_label='Time (ms)'
				bokehfig.yaxis.axis_label='X gaze'


				mb_container.append(components(plot, CDN))
				mycontainer[cit].scriptX, mycontainer[cit].divX = components(plot, CDN)
				# container[cit]['script'], container[cit]['div'], = components(plot, CDN)
				# container[]
				# cit += 1

				
				## plot Y coordinate for both eyes
				
				bokehfig = figure(title = 'Trial {0}. Y coordinate. Right eye shifted {1}'.format(trial+1,shiftval))
				bokeh_plot_gaze(bokehfig, ds.timestamps[idx_start:idx_end], ds.leftgazeY[idx_start:idx_end], ds.rightgazeY[idx_start:idx_end], 
					trial_ts = trial_ts, label1 = 'left eye', label2 = 'right eye', X_color = left_rgb, Y_color = right_rgb, shiftval = shiftval, plotrange = plotrange)

				plot = bokeh_plotTC(bokehfig, ds.left_trial[trial], Tmax, YvalsA, left_rgb, change_axis=1, label = 'Left input')		# plot TC. left press
				plot = bokeh_plotTC(bokehfig, ds.right_trial[trial], Tmax, YvalsB, right_rgb, change_axis=1, label = 'Right input')		# plot TC. left press
				
				bokehfig.xaxis.axis_label='Time (ms)'
				bokehfig.yaxis.axis_label='Y gaze'

				mb_container.append(components(plot, CDN))
				mycontainer[cit].scriptY, mycontainer[cit].divY = components(plot, CDN)
				# container[cit]['script'], container[cit]['div'], = components(plot, CDN)
				

				if createvideoYN and trial in videofortrials: 
					videoname = '{0}_{1}_Trial_{2}_XYplotmoviepy.mp4'.format(ds.expname, ds.subjectname, trial+1)

					# filter data per 5
					samples = 100
					ts  = movingaverage(ds.timestamps[idx_start:idx_end], samples)
					lgx = movingaverage(ds.leftgazeX[idx_start:idx_end],samples)
					lgy = movingaverage(ds.leftgazeY[idx_start:idx_end],samples)

					# t = time.time()
					# createvideo(ts, lgx, lgy, videoname = videoname)
					# elapsed = time.time() - t
					# print 'creating a video with matplotlib took: {0} seconds'.format(elapsed)

					t = time.time()
					createvideowithmoviepy(ts, lgx, lgy, videoname = videoname)
					elapsed = time.time() - t
					print 'creating a video with matplotlib took: {0} seconds'.format(elapsed)


					# sys.exit()

					mycontainer[cit].XYvideolink = videoname

					# sys.exit()

				if create_highangle_videoYN and trial in videofortrials:
					videoname = '{0}_{1}_Trial_{2}_HAplot.mp4'.format(ds.expname, ds.subjectname, trial+1)
					print 'creating high angle video'
					create_highangle_video(ds.timestamps[idx_start:idx_end], ds.leftgazeX[idx_start:idx_end], ds.rightgazeX[idx_start:idx_end], videoname = 'highanglevideo.mp4')

					mycontainer[cit].HAvideolink = videoname
					

				# sys.exit()


				
				cit += 1
				it += 2 																					# increase iterator

		if not forshow0_forsave1:
			# plt.show()
			pass

		###########################################	
		# Create Interactive html
		###########################################
		fWebName = '{0}.html'.format(os.path.splitext(os.path.split(f)[1]))[0]
		if create_ihtml_bokeh:
			## copy header
			with open(fWeb_HEADER,'r') as head:
				header = head.read()

			with open(fWebName, 'w' ) as fWebID:															#
				fWebID.seek(0)
				# create_interactive_html(datastruct = ds, mb = mb_container, fWebID=fWebID, DIR_IN = DIR_IN, DIR_OUT = DIR_OUT, fWeb_HEADER = header)
				create_interactive_html2(datastruct = ds, cont = mycontainer, fWebID=fWebID, DIR_IN = DIR_IN, DIR_OUT = DIR_OUT, fWeb_HEADER = header)

			print 'html save as {0}'.format(fWebName)


		###########################################
		# Create html
		###########################################
		if forshow0_forsave1:

			## check if html file name already exists
			if os.path.exists(fWebName):																	# if html file exists
				result = askquestion("Message", "HTML name already exists. Do you want to overwrite it?")	# overwrite it?
				if result == 'no':																			# if no overwrite it
					fWeb_NAME = askstring('HTML name exists','write new html file name')					# write new name

			with open(fWebName, 'w' ) as fWebID:															#
				add_figs_in_html(datastruct = ds, fWebID=fWebID, DIR_IN = DIR_IN, DIR_OUT = DIR_OUT, fWeb_HEADER = header)		#
				# fWebID.write('\n</table>') 																	# close table (it is opened in add_figs_in_html)

	pass

def add_figs_in_html(datastruct = None, fWebID='', DIR_IN = '', DIR_OUT = '', width = 800, height = 800):

	fWebID.write('\n<p><b>Experiment:</b> {0}\t<b>Subject:</b> {1}</p>'.format(datastruct.expname, datastruct.subjectname)) 	# write the experiment and subject's name

	fWebID.write('\n<table>') 																				# create new table

	for i in ['X', 'Y']:
		fWebID.write('\n<tr>') 																				# create new row
		
		# Image 1: all the gaze

		imgname = '*_{0}_{1}_alltrials_{2}gaze.{3}'.format(datastruct.expname,datastruct.subjectname,i,outformat)		# format of name
		img = glob.glob(os.path.join(DIR_OUT,imgname))[0]  																# get full path/name of image

		fWebID.write('\n<td>')																				# create new cell
		fWebID.write('\n<img width="{0}"" height="{1}" src="{2}">'.format(width, height, img))				# create image
		fWebID.write('\n</td>')																				# close cell

		# Image 2: trials
		
		imgname = '*{0}_{1}_input_and_{2}gaze-trial_*.{3}'.format(datastruct.expname, datastruct.subjectname, i, outformat)	# format of name
		trialimgs = glob.glob(os.path.join(DIR_OUT,imgname))																# get all the images that have gaze_and_input_trial

		for img in trialimgs:																				# for each of those
			fWebID.write('\n<td>')																			# create new cell	
			fWebID.write('\n<img width="{0}"" height="{1}" src="{2}">'.format(width, height, img)) 			# create image
			fWebID.write('\n</td>')																			# close cell


		## add here more images


		fWebID.write('\n</tr>') 																			# close row

	pass

class DataStruct():
	def __init__(self):
		
		self.leftgazeX = []
		self.leftgazeY = []
		self.rightgazeX = []
		self.rightgazeY = []

		self.left_ts = []
		self.right_ts = []

		self.trial_ts = []

		self.timestamps = []

		self.numtrials = 0

		self.left_trial = []
		self.right_trial = []

		self.expname = ''
		self.subjectname = ''
		self.filename = ''

		pass

def read_data(datastruct, datafile = '', right_keys  = ['4'], left_keys   = ['1'], epsilon = 0.0123, plotrange = [-0.1,1.1], shiftval = 0.05):
	###########################################
	# Constants: indexes of colums in data file
	###########################################
	idx_tms = 0		# index for time stamps
	idx_lgX = 7		# index for left gaze X
	idx_lgY = 8 	# index for left gaze Y
	idx_rgX = 20 	# index for right gaze X
	idx_rgY = 21 	# index for right gaze Y

	########################################
	# Read data file
	#######################################
	datastruct.filename = os.path.split(datafile)[1]
	data = np.genfromtxt(datafile, delimiter="\t", dtype=None, usecols=np.arange(0,27))	# read data file

	########################################
	# Filter headers, data and input events
	#######################################

	headers = data[0,:]													# get headers
	
	timestamps_all = np.array(map(float, data[1:,idx_tms]))				# get ALL time stamps, including events'. convert from string to float
	max_ts_loc = np.argmax(timestamps_all[0:-1])						# location of maximum timestamp

	datastruct.timestamps = timestamps_all[0:max_ts_loc + 1 ]			# get time stamps of the eye tracker data
	
	# eyetracker data
	datastruct.leftgazeX = np.array(map(float, data[1:max_ts_loc + 2, idx_lgX]))	# get left gaze X data
	datastruct.leftgazeY = np.array(map(float, data[1:max_ts_loc + 2, idx_lgY]))	# get left gaze Y data
	datastruct.rightgazeX = np.array(map(float, data[1:max_ts_loc + 2, idx_rgX]))	# get right gaze X data
	datastruct.rightgazeY = np.array(map(float, data[1:max_ts_loc + 2, idx_rgY]))	# get right gaze Y data

	###############################################
	# Map values outside of range to the boundaries
	###############################################
	datastruct.leftgazeX[plotrange[0] > datastruct.leftgazeX] = plotrange[0]; datastruct.leftgazeX[plotrange[1] < datastruct.leftgazeX] = plotrange[1]
	datastruct.leftgazeY[plotrange[0] > datastruct.leftgazeY] = plotrange[0]-shiftval; datastruct.leftgazeY[plotrange[1] < datastruct.leftgazeY] = plotrange[1]-shiftval
	datastruct.rightgazeX[plotrange[0] > datastruct.rightgazeX] = plotrange[0]; datastruct.rightgazeX[plotrange[1] < datastruct.rightgazeX] = plotrange[1]
	datastruct.rightgazeY[plotrange[0] > datastruct.rightgazeY] = plotrange[0]; datastruct.rightgazeY[plotrange[1] < datastruct.rightgazeY] = plotrange[1]

	# trial events
	# trial_ts = []														# Trial time stamps
	for it in range(max_ts_loc+2,len(timestamps_all)+1):				# 
		if data[it, 1] == 'TrialEvent':									# For each 
			ts = data[it, 0].astype(np.float)							#
			datastruct.trial_ts.append(ts) 								#

		if data[it, 1] == 'InfoEvent' and data[it, 2] == 'ExpName':		# If there's an InfoEvent and ExpName
			datastruct.expname = data[it, 3]							# get experiment name

		if data[it, 1] == 'InfoEvent' and data[it, 2] == 'SubjectName':	# If there's an InfoEvent and SubjectName
			datastruct.subjectname = data[it, 3]						# get subject name
	
	datastruct.numtrials = len(datastruct.trial_ts)/2 					# compute number of trials
	
	# input events
	input_ts = []														# Input time stamps
	in_code  = []

	left_press = np.zeros(0)
	left_relea = np.zeros(0)
	right_press = np.zeros(0)
	right_relea = np.zeros(0)

	for it in range(max_ts_loc+2,len(timestamps_all)+1):				# 
		if data[it, 1] == 'InputEvent':									# For each input event
			ts = data[it, 0].astype(np.float)							# get time stamps

			in_type = data[it, 2].astype('str')#.astype(np.float)		# get input type
			in_id   = data[it, 3]#.astype(np.float)						# get input id

			if 'DW' in in_type and in_id in left_keys:					# Add time stamps
				left_press = np.append(left_press, ts)					# of left buttons
			if 'UP' in in_type and in_id in left_keys:					# 
				left_relea = np.append(left_relea, ts)					#

			if 'DW' in in_type and in_id in right_keys:					# Add time stamps
				right_press = np.append(right_press, ts)				# of right buttons
			if 'UP' in in_type and in_id in right_keys:					#
				right_relea = np.append(right_relea, ts)				#

	# Check input events

	# ## Get input in each trial
	x, y, z = 2, 0, datastruct.numtrials 														# size of matrix
	datastruct.left_trial = [[[0 for k in xrange(x)] for j in xrange(y)] for i in xrange(z)]	# matrix for left input of each trial
	datastruct.right_trial = [[[0 for k in xrange(x)] for j in xrange(y)] for i in xrange(z)]	# matrix for right input of each trial

	it = 0 															# iterator
	for trial in range(datastruct.numtrials): 						# for each trial
		start = datastruct.trial_ts[it]								# start of trial value
		end   = datastruct.trial_ts[it+1]							# end of trial value

		lp = [i for i in left_press if start<i<end]					# get left presses in trial

		for press in lp:											# for each left press
			val, idx_start = find_nearest_above(left_relea, press)	# look for the nearest above left release
			
			if val is not None:
				release = np.minimum(end,val)						# compare nearest above to end of trial, get minimum
			else:
				release = end

			datastruct.left_trial[trial].append([press, release]) 	# add press and release times to matrix

		rp = [i for i in right_press if start<i<end]				# get left presses in trial

		for press in rp:											# for each right press
			val, idx_start = find_nearest_above(right_relea, press)	# look for the nearest above right release
			
			if val is not None:
				release = np.minimum(end,val)						# compare nearest above to end of trial, get minimum
			else:
				release = end
			datastruct.right_trial[trial].append([press, release])	# add press and release times to matrix

		it += 2 													# increase iterator

		for item in datastruct.left_trial[trial]:
			datastruct.left_ts.append(item)
		for item in datastruct.right_trial[trial]:
			datastruct.right_ts.append(item)

	return datastruct


def read_data2(datastruct, datafile = '', right_keys  = ['4'], left_keys   = ['1'], epsilon = 0.0123, plotrange = [-0.1,1.1], shiftval = 0.05):
	###########################################
	# Constants: indexes of colums in data file
	###########################################
	idx_tms = 0		# index for time stamps
	idx_lgX = 7		# index for left gaze X
	idx_lgY = 8 	# index for left gaze Y
	idx_rgX = 20 	# index for right gaze X
	idx_rgY = 21 	# index for right gaze Y

	#######################################
	# Read data file
	#######################################
	datastruct.filename = os.path.split(datafile)[1]
	try:
		data = np.genfromtxt(datafile, delimiter="\t", dtype=None, usecols=np.arange(0,31))	# read data file
	except ValueError:
		data = np.genfromtxt(datafile, delimiter="\t", dtype=None, usecols=np.arange(0,6))	# read data file

	#######################################
	# Determine if datafile contains
	# eyetracker data or just input (mouse)
	#######################################
	numofcolumns  = np.shape(data)[1]			# get number of columns

	if numofcolumns == 31: 													# eyetracker and input data
		
		######################
		# Read eyetracker data
		######################
		datastruct.timestamps = np.array(map(float, data[1:,idx_tms]))		# get time stamps of the eye tracker data

		# eyetracker data
		datastruct.leftgazeX 	= np.array(map(float, data[1:, idx_lgX]))	# get left gaze X data
		datastruct.leftgazeY 	= np.array(map(float, data[1:, idx_lgY]))	# get left gaze Y data
		datastruct.rightgazeX 	= np.array(map(float, data[1:, idx_rgX]))	# get right gaze X data
		datastruct.rightgazeY 	= np.array(map(float, data[1:, idx_rgY]))	# get right gaze Y data

		# Map values outside of range to the boundaries
		datastruct.leftgazeX[plotrange[0] > datastruct.leftgazeX] = plotrange[0]; datastruct.leftgazeX[plotrange[1] < datastruct.leftgazeX] = plotrange[1]
		datastruct.leftgazeY[plotrange[0] > datastruct.leftgazeY] = plotrange[0]-shiftval; datastruct.leftgazeY[plotrange[1] < datastruct.leftgazeY] = plotrange[1]-shiftval
		datastruct.rightgazeX[plotrange[0] > datastruct.rightgazeX] = plotrange[0]; datastruct.rightgazeX[plotrange[1] < datastruct.rightgazeX] = plotrange[1]
		datastruct.rightgazeY[plotrange[0] > datastruct.rightgazeY] = plotrange[0]; datastruct.rightgazeY[plotrange[1] < datastruct.rightgazeY] = plotrange[1]

		# Tobii gives data from 0 to 1, we want it from -1 to 1:
		datastruct.leftgazeX 	= 2 * datastruct.leftgazeX 	- 1
		datastruct.leftgazeY 	= 2 * datastruct.leftgazeY 	- 1
		datastruct.rightgazeX 	= 2 * datastruct.rightgazeX - 1
		datastruct.rightgazeY 	= 2 * datastruct.rightgazeY - 1

	######################
	# Read input data
	######################
	
	# Constants: indexes of colums for events
	idx_ets = numofcolumns - 6	# events time stamps 	index
	idx_enm = numofcolumns - 5 	# events name 			index
	idx_etp = numofcolumns - 4	# events type 			index
	idx_eid = numofcolumns - 3	# events id 			index
	idx_evl = numofcolumns - 2	# events code 			index
	idx_ect = numofcolumns - 1	# events counter		index

	idx_ets = numofcolumns - 4	# events time stamps 	index
	idx_enm = numofcolumns - 3 	# events name 			index
	idx_etp = numofcolumns - 2	# events type 			index
	idx_eid = numofcolumns - 1	# events id 			index
	# idx_evl = numofcolumns - 2	# events code 			index
	# idx_ect = numofcolumns - 1	# events counter		index

	left_press = np.zeros(0)
	left_relea = np.zeros(0)
	right_press = np.zeros(0)
	right_relea = np.zeros(0)

	# get valid values (ignore cells that contain '-')
	ets = [x for x in data[1:,idx_ets] if x != '-']						# get event time stamps

	for it in range(1,len(ets)+1):											# for each event
		ts = ets[it-1].astype(np.float)									# get time stamp
					 													# and see its type.
		if data[it, idx_enm] == 'TrialEvent':							# if it is a trial event,
			datastruct.trial_ts.append(ts) 								# append the time stamp

		# if data[it, idx_etp] == 'InfoEvent':							# If there's an InfoEvent
		# 	if data[it, idx_ed] == 'ExpName':							# and ExpName
		# 		datastruct.expname = data[it, idx_evl]					# get experiment name
		# 	if data[it, idx_ed] == 'SubjectName':						# or SubjectName
		# 		datastruct.subjectname = data[it, idx_evl]				# get subject name

		if data[it, idx_enm] == 'InputEvent':							# for each input event	
			in_type = data[it, idx_enm].astype('str')					# get input type
			in_name = data[it, idx_enm].astype('str')					# get input type
			in_type = data[it, idx_etp].astype('str')					# get input id
			in_id	= data[it, idx_eid].astype('str')					# get input value

			if 'DW' in in_type and in_id in left_keys:					# Add time stamps
				left_press = np.append(left_press, ts)					# of left buttons
			if 'UP' in in_type and in_id in left_keys:					# 
				left_relea = np.append(left_relea, ts)					#

			if 'DW' in in_type and in_id in right_keys:					# Add time stamps
				right_press = np.append(right_press, ts)				# of right buttons
			if 'UP' in in_type and in_id in right_keys:					#
				right_relea = np.append(right_relea, ts)				#

	datastruct.numtrials = len(datastruct.trial_ts)/2 					# compute number of trials

	# Check input events

	# ## Get input in each trial
	x, y, z = 2, 0, datastruct.numtrials 														# size of matrix
	datastruct.left_trial = [[[0 for k in xrange(x)] for j in xrange(y)] for i in xrange(z)]	# matrix for left input of each trial
	datastruct.right_trial = [[[0 for k in xrange(x)] for j in xrange(y)] for i in xrange(z)]	# matrix for right input of each trial

	it = 0 															# iterator
	for trial in range(datastruct.numtrials): 						# for each trial
		start = datastruct.trial_ts[it]								# start of trial value
		end   = datastruct.trial_ts[it+1]							# end of trial value

		lp = [i for i in left_press if start<i<end]					# get left presses in trial

		for press in lp:											# for each left press
			val, idx_start = find_nearest_above(left_relea, press)	# look for the nearest above left release
			
			if val is not None:
				release = np.minimum(end,val)						# compare nearest above to end of trial, get minimum
			else:
				release = end

			datastruct.left_trial[trial].append([press, release]) 	# add press and release times to matrix

		rp = [i for i in right_press if start<i<end]				# get left presses in trial

		for press in rp:											# for each right press
			val, idx_start = find_nearest_above(right_relea, press)	# look for the nearest above right release
			
			if val is not None:
				release = np.minimum(end,val)						# compare nearest above to end of trial, get minimum
			else:
				release = end
			datastruct.right_trial[trial].append([press, release])	# add press and release times to matrix

		it += 2 													# increase iterator

		for item in datastruct.left_trial[trial]:
			datastruct.left_ts.append(item)
		for item in datastruct.right_trial[trial]:
			datastruct.right_ts.append(item)

	return datastruct

def plotTC(figure, time_stamps, time_max, Y_vals, color, change_axis = 0, label = ''):
	"""
	Plot time-course of perceptual alternation of ONE percept (left or right)
	Arguments:
	- figure: handle to the figure (or subplot) where TC should be drawn
	- time_stamps: a Nx2 matrx. Each row is pair [time_press, time_release] of
		a mouse/key event (percept start and end)
	- time_max: xmax value (for axis ([xmin, xmax, ymin, ymax]) call)
	- Y_vals: 1x4 vector with Yon, Yoff and ymin, ymax values
	- color: a 1x3 vector with RGB values of the plot line color
	- change_axis: if 1, changes the x and y axis using time_max and Y_vals
	- label: name to appear in legend
	"""
	ymin = Y_vals[2]
	ymax = Y_vals[3]

	# tiny = time_max/1000 # tiny dx to draw 'vertical' lines in TC
	tiny = 0

	if change_axis: figure.axis([0, time_max, ymin, ymax])

	for i in range(len(time_stamps)):
		figure.plot(time_stamps[i], [Y_vals[0], Y_vals[1]], color = color, label = label)
		figure.plot([time_stamps[i][0]-tiny, time_stamps[i][0]], [ymin, Y_vals[0]], color = color, linestyle=':')
		figure.plot([time_stamps[i][1]-tiny, time_stamps[i][1]], [ymin, Y_vals[1]], color = color, linestyle=':')
	pass

	handles, labels = plt.gca().get_legend_handles_labels()
	by_label = OrderedDict(zip(labels, handles))	
	figure.legend(by_label.values(), by_label.keys(), loc='best')

	return figure


def find_nearest_above(array, value):
	diff = array - value
	mask = np.ma.less_equal(diff, 0)
    # We need to mask the negative differences and zero
    # since we are looking for values above
	if np.all(mask):
		return None, None # returns None if target is greater than any value
	masked_diff = np.ma.masked_array(diff, mask)

	idx = masked_diff.argmin()
	val = array[idx]
	
	if val < value:		# if there's no value above
		val = -1 		# use -1 for val
		idx = 0 		# and 0 for idx


	return val, idx

def plot_gaze(figure, timestamps, gazeX, gazeY, label1 = '', label2 = '',trial_ts = [], X_color = (1.0, 0., 0.), Y_color = (1.0, 0., 0.), shiftval = 0.05, 
	plotrange = [-0.1,1.1], plotinput = 0, xaxislabel = '', yaxislabel = ''):

	figure.scatter(timestamps,gazeX,marker='x',color="red",label=label1,facecolors='none', edgecolors=X_color)		# plot
	figure.scatter(timestamps,gazeY,color="blue",label=label2,facecolors='none', edgecolors=Y_color)				# plot

	for event in trial_ts:													# for each event time stamp
		figure.plot((event, event), (plotrange[0],plotrange[1]), 'k-')		# plot a vertical line: plt.plot((x1,x2),(y1,y2),'k-')

	figure.set_xlabel(xaxislabel)											# label for X axis
	figure.set_ylabel(yaxislabel)											# label for Y axis
	figure.legend(loc='best')												# set the place of the legend	

	figure.set_ylim([plotrange[0],plotrange[1]+shiftval])
	

	return figure

def plot_gaze2(figure, timestamps, gazeX, label = '', trial_ts = [], color = (1.0, 0., 0.), shiftval = 0.05,	plotrange = [-0.1,1.1], plotinput = 0, xaxislabel = '', yaxislabel = ''):

	figure.scatter(timestamps,gazeX,marker='x',color="red",label=label1,facecolors='none', edgecolors=X_color)		# plot

	for event in trial_ts:													# for each event time stamp
		figure.plot((event, event), (plotrange[0],plotrange[1]), 'k-')		# plot a vertical line: plt.plot((x1,x2),(y1,y2),'k-')

	# figure.set_xlabel(xaxislabel)											# label for X axis
	# figure.set_ylabel(yaxislabel)											# label for Y axis
	# figure.legend(loc='best')												# set the place of the legend	

	# figure.set_ylim([plotrange[0],plotrange[1]+shiftval])

	return figure

def bokeh_plot_gaze(figure, timestamps, gazeX, gazeY, label1 = '', label2 = '',trial_ts = [], X_color = (1.0, 0., 0.), Y_color = (1.0, 0., 0.), shiftval = 0.05, 
	plotrange = [-0.1,1.1], plotinput = 0, xaxislabel = '', yaxislabel = ''):

	figure.scatter(timestamps,gazeX,marker='x',color=rgb2hex(X_color),legend=label1,facecolors='none', edgecolors=rgb2hex(X_color))		# plot
	figure.scatter(timestamps,gazeY,color=rgb2hex(Y_color),legend=label2,facecolors='none', edgecolors=rgb2hex(Y_color))				# plot

	for event in trial_ts:																			# for each event time stamp
		figure.line((event, event), (plotrange[0],plotrange[1]), 'k-', color = rgb2hex((0,0,0)))	# plot a vertical line: plt.plot((x1,x2),(y1,y2),'k-')

	# figure.set_xlabel(xaxislabel)											# label for X axis
	# figure.set_ylabel(yaxislabel)											# label for Y axis
	# figure.legend(loc='best')												# set the place of the legend	

	# figure.set_ylim([plotrange[0],plotrange[1]+shiftval])
	

	return figure

def bokeh_plotTC(figure, time_stamps, time_max, Y_vals, color, change_axis = 0, label = ''):
	"""
	Plot time-course of perceptual alternation of ONE percept (left or right)
	Arguments:
	- figure: handle to the figure (or subplot) where TC should be drawn
	- time_stamps: a Nx2 matrx. Each row is pair [time_press, time_release] of
		a mouse/key event (percept start and end)
	- time_max: xmax value (for axis ([xmin, xmax, ymin, ymax]) call)
	- Y_vals: 1x4 vector with Yon, Yoff and ymin, ymax values
	- color: a 1x3 vector with RGB values of the plot line color
	- change_axis: if 1, changes the x and y axis using time_max and Y_vals
	- label: name to appear in legend
	"""
	ymin = Y_vals[2]
	ymax = Y_vals[3]

	# tiny = time_max/1000 # tiny dx to draw 'vertical' lines in TC
	tiny = 0

	# if change_axis: figure.axis([0, time_max, ymin, ymax])
	# if change_axis: figure.x_range = [0, time_max]

	color = rgb2hex(color)

	for i in range(len(time_stamps)):
		figure.line(time_stamps[i], [Y_vals[0], Y_vals[1]], color = color, legend = label)
		figure.line([time_stamps[i][0]-tiny, time_stamps[i][0]], [ymin, Y_vals[0]], color = color, line_dash = 'dotted')
		figure.line([time_stamps[i][1]-tiny, time_stamps[i][1]], [ymin, Y_vals[1]], color = color, line_dash = 'dotted')
	pass

	# handles, labels = plt.gca().get_legend_handles_labels()
	# by_label = OrderedDict(zip(labels, handles))	
	# figure.legend(by_label.values(), by_label.keys(), loc='best')

	return figure

def rgb2hex(color):

	if max(color) <= 1:
		color = (np.array(color) * 255).astype(int).tolist()
	
	r = max(0, min(color[0] , 255))
	g = max(0, min(color[1] , 255))
	b = max(0, min(color[2] , 255))

	return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)

class my_bokeh_html_container():
	def __init__(self):
		self.scripts = []
		self.divs = []

	def append(self,a):
		self.scripts.append(a[0]) 	# script
		self.divs.append(a[1])		# div


class html_container():
	def __init__(self):
		self.scriptX = []
		self.divX = []

		self.scriptY = []
		self.divY = []

		self.XYvideolink = []	# relative path to the x,y gaze video
		self.HAvideolink = []	# relative path to the high angle video


	def function(self):
		pass

def create_interactive_html(datastruct = None, mb = None, fWebID='', DIR_IN = '', DIR_OUT = '', fWeb_HEADER = ''):

	fWebID.write(fWeb_HEADER)			# add header

	for script in mb.scripts:	# add scripts
		fWebID.write('\n\n\t\t')		# identation
		fWebID.write(script)			# script

	fWebID.write('\n\t</head>')			# end of head (identation)	

	fWebID.write('\n\t</body>')			# open body	
	
	fWebID.write('\n\t\t<p><b>Experiment:</b> {0}\t<b>Subject:</b> {1}</p>'.format(datastruct.expname, datastruct.subjectname)) 	# write the experiment and subject's name

	# fWebID.write('\n\t\t<table>') 																				# create new table
	for div in mb.divs:
		# fWebID.write('\n\t\t\t<tr>') 																				# create new row
		# fWebID.write('\n\t\t\t\t<td>')																				# create new cell
		fWebID.write(div)			# div
		# fWebID.write('\n\t\t\t\t</td>')																				# create new cell
		# fWebID.write('\n\t\t\t</tr>') 																				# create new row

	fWebID.write('\n\t</body>')			# close body	
	fWebID.write('\n</html>')			# close html




	# fWebID.write('\n<p><b>Experiment:</b> {0}\t<b>Subject:</b> {1}</p>'.format(datastruct.expname, datastruct.subjectname)) 	# write the experiment and subject's name

	# fWebID.write('\n<table>') 																				# create new table

	# for i in range(len(mb)):
	# 	fWebID.write('\n<tr>') 																				# create new row

	# for i in ['X', 'Y']:
	# 	fWebID.write('\n<tr>') 																				# create new row
	# 	fWebID.write('\n<td>')																				# create new cell
	# 	fWebID.write()
	# 	fWebID.write('\n<img width="{0}"" height="{1}" src="{2}">'.format(width, height, img))				# create image
	# 	fWebID.write('\n</td>')																				# close cell

	# 	# Image 1: all the gaze

	# 	imgname = '*_{0}_{1}_alltrials_{2}gaze.{3}'.format(datastruct.expname,datastruct.subjectname,i,outformat)		# format of name
	# 	img = glob.glob(os.path.join(DIR_OUT,imgname))[0]  																# get full path/name of image

	# 	fWebID.write('\n<td>')																				# create new cell
	# 	fWebID.write('\n<img width="{0}"" height="{1}" src="{2}">'.format(width, height, img))				# create image
	# 	fWebID.write('\n</td>')																				# close cell

	# 	# Image 2: trials
		
	# 	imgname = '*{0}_{1}_input_and_{2}gaze-trial_*.{3}'.format(datastruct.expname, datastruct.subjectname, i, outformat)	# format of name
	# 	trialimgs = glob.glob(os.path.join(DIR_OUT,imgname))																# get all the images that have gaze_and_input_trial

	# 	for img in trialimgs:																				# for each of those
	# 		fWebID.write('\n<td>')																			# create new cell	
	# 		fWebID.write('\n<img width="{0}"" height="{1}" src="{2}">'.format(width, height, img)) 			# create image
	# 		fWebID.write('\n</td>')																			# close cell


	# 	## add here more images


	# 	fWebID.write('\n</tr>') 																			# close row

	pass

def create_interactive_html2(datastruct = None, cont = None, fWebID='', DIR_IN = '', DIR_OUT = '', fWeb_HEADER = ''):
	videowidth, videoheight = 800,600

	fWebID.write(fWeb_HEADER)										# add header
	for i in range(len(cont)):										# for each element in container
		# fWebID.write('\n\t\t')										# write identation
		script = cont[i].scriptX									# get script for X coordinates
		fWebID.write('\n\t\t{0}'.format(str(script)))				# write script

		# fWebID.write('\n\n\t\t')									# write identation
		script = cont[i].scriptY									# get script for Y coordinates
		fWebID.write('\n\t\t{0}'.format(str(script)))				# write script


	fWebID.write('\n\t</head>')										# write end of head tag (identation)	
	fWebID.write('\n\t</body>')										# open body	tag
	
	fWebID.write(																					# write experiment, 
		'\n\t\t<p><b>Experiment:</b> {0}\t<b>Subject:</b> {1}\t<b>Filename:</b> {2}</p>'.format(	# subject and file
		datastruct.expname, datastruct.subjectname, datastruct.filename)) 							# names


	# write plots
	fWebID.write('\n\t\t<table>') 									# create new table
	
	
	# Write X data in a row
	fWebID.write('\n\t\t\t<tr>') 									# create new row (plots in different colums)
	for i in range(len(cont)):										# for each element in container
		divX = cont[i].divX											# get div for X coordinates
		
		fWebID.write('\n\t\t\t\t<td>')								# create new cell (colum)
		fWebID.write('\n\t\t\t\t\t')								# write identation
		fWebID.write(str(divX))										# write div for i script
		fWebID.write('\n\t\t\t\t</td>')								# close cell tag
	
	fWebID.write('\n\t\t\t</tr>') 									# close row tag

	# Write Y data in a row
	fWebID.write('\n\t\t\t<tr>') 									# create new row tag
	for i in range(len(cont)):										# for each element in container
		divY = cont[i].divY											# get div for Y coordinates

		fWebID.write('\n\t\t\t\t<td>')								# create new cell		
		fWebID.write('\n\t\t\t\t\t')
		fWebID.write(str(divY))										# write div for i script
		fWebID.write('\n\t\t\t\t</td>')								# close new cell
	
	fWebID.write('\n\t\t\t</tr>') 									# close row tag

	# Write video XY links in a row
	fWebID.write('\n\t\t\t<tr>') 									# create new row tag
	for i in range(len(cont)):										# for each element in container
		videolink = cont[i].XYvideolink								# get div for Y coordinates

		fWebID.write('\n\t\t\t\t<td>')								# create  cell		
		fWebID.write('\n\t\t\t\t\t')
		
		if videolink: 
			fWebID.write('<video width="{0}" height="{1}" controls>'.format(videowidth, videoheight))
			fWebID.write('\n\t\t\t\t\t\t')
			fWebID.write('<source src="{0}" type="video/mp4">'.format(str(videolink)))					# write div for i script
			fWebID.write('Your browser does not support HTML5 video.')
			fWebID.write('\n\t\t\t\t\t</video>')
			
		fWebID.write('\n\t\t\t\t</td>')								# close cell
	
	fWebID.write('\n\t\t\t</tr>') 									# close row tag



	# Write video HA links in a row
	fWebID.write('\n\t\t\t<tr>') 									# create new row tag
	for i in range(len(cont)):										# for each element in container
		videolink = cont[i].HAvideolink								# get div for Y coordinates

		fWebID.write('\n\t\t\t\t<td>')								# create  cell		
		fWebID.write('\n\t\t\t\t\t')
		
		if videolink: 
			fWebID.write('<video width="{0}" height="{1}" controls>'.format(videowidth, videoheight))
			fWebID.write('\n\t\t\t\t\t\t')
			fWebID.write('<source src="{0}" type="video/mp4">'.format(str(videolink)))			
			fWebID.write('Your browser does not support HTML5 video.')
			fWebID.write('\n\t\t\t\t\t</video>')
			
		fWebID.write('\n\t\t\t\t</td>')								# close cell
	
	fWebID.write('\n\t\t\t</tr>') 									# close row tag



	############
	# Put more things here
	############


	fWebID.write('\n\t</body>')			# close body	
	fWebID.write('\n</html>')			# close html

	pass


def plot_XYeye(figure,x,y,ntimestamp = '',label='', color = (1.0,0.0,0.0), plotrange = [-0.1,1.1], anotation = 0, text = None):

	figure.scatter(x,y,marker = 'x', color = color, label = label)
	
	figure.set_ylim([0,1])
	figure.set_xlim([0,1])
	# if anotation: plt.annotate('({0},{1})'.format(x,y), xy = (x,y), xytext = (x, y-0.1))
	
	if anotation and text is not None:
		text.set_text('({0},{1})'.format( '%.2f' % (x),'%.2f' % (y)))
		text.set_position((x-0.05,y-0.05))

	return figure

def creategif(datafileslist = '', imfolder = 'im2gif', gifname = 'outputgif2.gif', format = 'jpg'):
	import subprocess

	for datafile in datafileslist:											# for each data file
		print 'datafile used: ... {0}\n'.format(datafile[-30:])				# print the name of the current data file 

		# create directory to save gif images
		if not os.path.exists(imfolder):
			os.makedirs(imfolder)

		ds = DataStruct()													# create new DataStruct instance
		ds = read_data(ds, datafile)										# read data and store in datastruct

		ntimestamp = 20
		it = 0 ######################################################################################################
		start = ds.trial_ts[it]												# start of trial value
		end = ds.trial_ts[it+1]												# end of trial value

		val, idx_start = find_nearest_above(ds.timestamps, start)			# find nearest above eyetracker time stamp

		idx_end = idx_start + ntimestamp #end

		ts = ds.timestamps[idx_start:idx_end]
		LgazeX = ds.leftgazeX[idx_start:idx_end]
		LgazeY = ds.leftgazeY[idx_start:idx_end]


		for n in range(ntimestamp):
			f, ax = plt.subplots()		
			Lx, Ly = LgazeX[n], LgazeY[n]

			plot_XYeye(ax,Lx,Ly)


			title = 'time stamp: {0}. frame: {1}'.format(ts[n], "%04d" % (n))
			ax.set_title(title)


			imname = '{0}_{1}_{2}.{3}'.format(ds.expname,ds.subjectname,"%04d" % (n), format)

			plt.savefig(os.path.join(imfolder,imname))


		# this creates the gif from command line not python, imagemagick is doing the gif
		delay = 20
		loop = 0
		imset = '{0}_{1}_*.{2}'.format(os.path.join(imfolder, ds.expname), ds.subjectname, format)
		# task = subprocess.Popen('convert -delay {0} -loop {1} {2}_{3}_*.{4} {5}'.format(delay, loop, os.path.join(imfolder, ds.expname), ds.subjectname, format, gifname))
		# task = subprocess.Popen(['C:\Program Files\ImageMagick-6.9.0-Q16\convert', '-delay', '{0}'.format(delay), '-loop', '{0}'.format(), 'im2gif/Plaid_v19_jl2_*.jpg', 'gifname.gif'])
		task = subprocess.Popen(['C:\Program Files\ImageMagick-6.9.0-Q16\convert', '-delay', '{0}'.format(delay), '-loop', '{0}'.format(loop), '{0}'.format(imset), '{0}'.format(gifname)])
		time.sleep(10

			)
		task.terminate()

		# # os.system('convert -delay {0} -loop {1} {2}_{3}_*.{4} {5}'.format(delay, loop, os.path.join(imfolder, ds.expname), ds.subjectname, format, gifname))
		# # convert -delay 20 -loop 0 Plaid_v19_jl2_*.jpg animation.gif


		# remove folder with images
		if os.path.exists(imfolder):

			import errno, stat, shutil

			def handleRemoveReadonly(func, path, exc):
			  excvalue = exc[1]
			  if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
			      os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
			      func(path)
			  else:
			      raise

			shutil.rmtree(imfolder, ignore_errors=False, onerror=handleRemoveReadonly)
			# shutil.rmtree(imfolder)		


	pass

def createmp4(timestamps, LgazeX, LgazeY, videoname = '', RgazeX = '', RgazeY = '', xlabel = '', plottitle = ''):
	import matplotlib.animation as animation
	print 'createmp4'

	ntimestamp = len(timestamps)
	
	def init():
		line1.set_data([], [])
		line2.set_data([], [])

		text.set_text('')
		annotation.set_text('')
		# annotation = plt.annotate('', xy=(0,0))
		# annotation.set_animated(True)

		return line1, line2, text, annotation

	def update_line(num, timestamps, gazeX, gazeY, line1, line2):
		ts = timestamps[num]
		x = gazeX[num]
		y = gazeY[num]
		line1.set_data([x-0.01,x+0.01], [y-0.01,y+0.01])
		line2.set_data([x-0.01,x+0.01], [y+0.01,y-0.01])

		text.set_text("timestamp: {0} frame: {1}".format(ts, num))

		# annotation = plt.annotate('({0},{1})'.format( '%.2f' % (x),'%.2f' % (y)), xy=(x-0.05,y-0.05))
		annotation.set_text('({0},{1})'.format( '%.2f' % (x),'%.2f' % (y)))
		annotation.set_position((x-0.05,y-0.05))

		return line1, line2, text, annotation


	fig1 = plt.figure()

	line1, = plt.plot([], [], 'r-')
	line2, = plt.plot([], [], 'r-')

	text = plt.text(0, 0, "timestamp: \tframe: ")
	annotation = plt.text(0, 0, "")

	# matplotlib.text.Text(x=0, y=0, text=u'', color=None, verticalalignment=u'baseline', horizontalalignment=u'left', multialignment=None, fontproperties=None, rotation=None, linespacing=None, rotation_mode=None, **kwargs)

	plt.xlim(0, 1)
	plt.ylim(0, 1)
	plt.xlabel(xlabel)
	plt.title(plottitle)
	line_ani = animation.FuncAnimation(fig1, update_line, ntimestamp, fargs=(timestamps, LgazeX, LgazeY, line1, line2), interval=500, blit=True, init_func = init)
	
	dpi = 100
	writer = animation.writers['ffmpeg'](fps=30)
	line_ani.save(videoname,writer=writer,dpi=dpi)

	# line_ani.save(videoname)
	#plt.show()

	# return fig1, 


	pass


def createvideo(timestamps, LgazeX, LgazeY, RgazeX = '', RgazeY = '', videoname = '', xlabel = '', plottitle = '', show_pos = 1):

	import matplotlib
	matplotlib.use("Agg", warn = False)
	import matplotlib.animation as manimation

	FFMpegWriter = manimation.writers['ffmpeg']
	metadata = dict(title='Movie Test', artist='Matplotlib', comment='Movie support!')
	writer = FFMpegWriter(fps=24, extra_args=['-vcodec', 'h264', '-pix_fmt', 'yuv420p'], metadata=metadata)

	fig = plt.figure()
	left_eye, = plt.plot([], [], 'k-o')
	# right_eye, = plt.plot([], [], 'k-o')

	plt.xlim(0, 1)
	plt.ylim(0, 1)

	plt.xlabel(xlabel)
	plt.title(plottitle)

	lpostext = fig.text(0, 0, "")
	# rpostext = fig.text(0, 0, "")

	frameinfo = fig.text(0, 0, "")

	with writer.saving(fig, videoname, 100):
	    for i in range(len(timestamps)):
			lx = LgazeX[i]
			ly = LgazeY[i]
			# rx = RgazeX[i]
			# ry = RgazeY[i]
			ts = timestamps[i]

			left_eye.set_data(lx, ly)
			# right_eye.set_data(rx, ry)
			
			if show_pos:
				lpostext.set_text('({0},{1})'.format( '%.2f' % (lx),'%.2f' % (ly)))
				lpostext.set_position((lx-0.05,ly-0.05))

				# rpostext.set_text('({0},{1})'.format( '%.2f' % (rx),'%.2f' % (ry)))
				# rpostext.set_position((rx-0.05,ry-0.05))

			frameinfo.set_text("timestamp: {0} frame: {1}".format(ts, i))

			writer.grab_frame()


def createvideowithmoviepy(timestamps, LgazeX, LgazeY, RgazeX = '', RgazeY = '', videoname = '', xlabel = '', plottitle = '', show_pos = 1):

	from moviepy.editor import VideoClip
	from moviepy.video.io.bindings import mplfig_to_npimage

	videofps = 120
	framerate = 120.0 							# framerate of tobii.
	duration = len(timestamps) / framerate		# compute duration in seconds

	def make_frame(i):
	# returns an image of the frame at time t
		plt.close('all')
		fig = plt.figure()
		left_eye, = plt.plot([], [], 'k-o')
		# right_eye, = plt.plot([], [], 'k-o')

		plt.xlim(0, 1)
		plt.ylim(0, 1)

		plt.xlabel(xlabel)
		plt.title(plottitle)

		lpostext = fig.text(0, 0, "")
		frameinfo = fig.text(0, 0, "")


		lx = LgazeX[i]
		ly = LgazeY[i]
		# rx = RgazeX[i]
		# ry = RgazeY[i]
		ts = timestamps[i]

		left_eye.set_data(lx, ly)
		# right_eye.set_data(rx, ry)
		
		if show_pos:
			lpostext.set_text('({0},{1})'.format( '%.2f' % (lx),'%.2f' % (ly)))
			lpostext.set_position((lx-0.05,ly-0.05))

		frameinfo.set_text("timestamp: {0} frame: {1}".format(ts, i))
		return mplfig_to_npimage(fig)

	animation = VideoClip(make_frame, duration=duration) # 3-second clip

	# For the export, many options/formats/optimizations are supported
	animation.write_videofile(videoname, fps=videofps) # export as video




def create_highangle_video(timestamps, Lgaze_array, Rgaze_array, videoname = ''):
	import matplotlib
	matplotlib.use("Agg", warn = False)	# warn = False will supress warnings
	import matplotlib.animation as manimation
	
	##########################
	# Initialize video writer 
	##########################

	FFMpegWriter = manimation.writers['ffmpeg']
	metadata = dict(title='highanglegazevideo', artist='Matplotlib', comment='Movie support!')
	writer = FFMpegWriter(fps=15, metadata=metadata)

	######################
	# Constants definition
	######################
	lpos = [-0.5, -1]																		# position of left eye
	rpos = [0.5, -1]																		# position of right eye

	lcolor = (1.0, 0., 0.)																	# left eye/gaze/line color
	rcolor = (0., 1.0, 0.)																	# right eye/gaze/line color

	eyesize = 20																			# size of eyes
	gazesize = 5																			# size of gaze

	xmin, xmax, ymin, ymax = -1, 1, -1, 1													# plot limits

	y_scrn = 0																				# y position of the dashed line in the middle (screen)


	fig = plt.figure()																		# initialize figure

	###############################################
	# Initialize Drawings (only the ones that move)
	################################################

	leg, = plt.plot([lpos[0], Lgaze_array[0]],[lpos[1], y_scrn], '--', color = lcolor)						# line from left eye to left gaze
	reg, = plt.plot([rpos[0], Rgaze_array[0]],[rpos[1], y_scrn], '--', color = rcolor)						# line from right eye to right gaze

	lgt, = plt.plot([Lgaze_array[0], 2*Lgaze_array[0] - lpos[0]],[y_scrn, ymax], '--', color = lcolor)		# line from left gaze to top of plot
	rgt, = plt.plot([Rgaze_array[0], 2*Rgaze_array[0] - rpos[0]],[y_scrn, ymax], '--', color = rcolor)		# line from right gaze to top of plot

	lg, = plt.plot(Lgaze_array[0],y_scrn, 'o', color = lcolor, markersize = gazesize)						# draw left gaze
	rg, = plt.plot(Rgaze_array[0],y_scrn, 'o', color = rcolor, markersize = gazesize)						# draw right gaze

	frameinfo = fig.text(0.1, 0.02, "")																			# frame information
	
	######################
	# Draw each frame
	######################
	with writer.saving(fig, videoname, 100):												# open video
		for i in range(len(timestamps)):													# create each frame
	    	
			lgaze = Lgaze_array[i]															# get left gaze for frame i
			rgaze = Rgaze_array[i]															# get right gaze for frame i

			ts = timestamps[i]																# get timestamp for i frame

			######################
			# Drawings
			######################
			plt.plot(lpos[0],lpos[1], 'o', color = lcolor, markersize = eyesize)			# draw left eye
			plt.plot(rpos[0],rpos[1], 'o', color = rcolor, markersize = eyesize)			# draw right eye

			plt.plot([-1, 1],[y_scrn, y_scrn],'k:')											# draw dashed line in the middle (screen)

			leg.set_data([lpos[0], lgaze],[lpos[1], y_scrn])								# update position of line from left eye to left gaze
			reg.set_data([rpos[0], rgaze],[rpos[1], y_scrn])								# update position of line from right eye to right gaze

			lgt.set_data([lgaze, 2*lgaze - lpos[0]],[y_scrn, ymax])							# update position of line from left gaze to top of plot
			rgt.set_data([rgaze, 2*rgaze - rpos[0]],[y_scrn, ymax])							# update position of line from right gaze to top of plot

			lg.set_data(lgaze,y_scrn)														# update position of left gaze
			rg.set_data(rgaze,y_scrn)														# update position of right gaze


			frameinfo.set_text("timestamp: {0} frame: {1}".format(ts, i))
			plt.axis([xmin, xmax, ymin, ymax]) 												# set axis limits: [xmin, xmax, ymin, ymax]

			writer.grab_frame()																# send frame to movie writer

	pass

def movingaverage(array, samples):
    window = np.ones(int(samples))/float(samples)
    return np.convolve(array, window, 'valid')

if __name__ == '__main__':
	"""
	Usage: python read_data_and_create_html.py DIR_IN DIR_OUT fWeb_NAME fWeb_HEADER DATE_TIME_format extension
	"""

	if len(sys.argv) < 2:
		print 'Choose which data files to analyze'
	else:
		pass
		# DIR_IN = sys.argv[1]
	
	## Define default parameters. DIR_IN and DIR_OUT must be created manually.
	DIR_IN = 'data'														# the folder where the script is should contain a folder called data
	DIR_OUT = 'figures'													# Where images will be saved
	fWeb_NAME = '_test.html'												# name of the html

	## Create GUI to open files
	Tk().withdraw() 													# we don't want a full GUI, so keep the root window from appearing
	datafileslist = askopenfilenames(title='Chose files to analyze') 	# show an "Open" dialog box and return the path to the selected file
	# datafileslist = ["C:/Users/NuEye/Google Drive/NuEyeUPF/RubinLabs_Experiments/Experiment01 - Plaid/data/test.txt"]
	# creategif(datafileslist = datafileslist)
	# createmp4(datafileslist = datafileslist)
	main(datafileslist = datafileslist, DIR_IN=DIR_IN, DIR_OUT = DIR_OUT, fWebName = fWeb_NAME, fWeb_HEADER = 'html_template.html')




	
	# main(DIR_IN=DIR_IN, DIR_OUT=DIR_OUT,fWeb_NAME=fWeb_NAME,fWeb_HEADER=fWeb_HEADER,DATE_TIME_format=DATE_TIME_format, extension=extension)