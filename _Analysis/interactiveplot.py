import glob 								# to list the files in directory
import sys									# to parse input
import numpy as np 							# to read data
import matplotlib.pyplot as plt 			# to plot
import os 									# to save figures in folder
import time 								# to name figures
import shutil 								# to delete folders

from collections import OrderedDict			# for plotTC

from Tkinter import Tk 						# for open file GUI
from tkFileDialog import askopenfilenames 	# for open file GUI
from tkSimpleDialog import askstring 		# if name of html exists,
from tkMessageBox import askquestion 		# ask new name

from bokeh.resources import CDN
from bokeh.embed import components, file_html
from bokeh import mpl
from bokeh.plotting import figure, output_file, show, VBox

def main(datafileslist = '', DIR_OUT='', fWeb_HEADER='html_template.html', DATE_TIME_format="%Y-%m-%d_%H.%M", input_extension = '*.txt',
	A_color = (1.0, 0., 0.), B_color = (0., 1.0, 0.), YvalsA=[0.80, 0.90, 0, 1], YvalsB=[0.75, 0.85, 0, 1],
	apply_fade = 1, fade_sec = 0.5, samplingfreq = 120.0, shiftval = 0.05, color_shift = [-0.3,0,0], plotrange = [-1.1,1.1], forshow0_forsave1 = 0,
	createvideoYN = 0, create_highangle_videoYN = 0, videofortrials = (0,-1), epsilon = 0.0123, A_code = 1, B_code = 4, trial_code = 8):

	# Scale Yvals to plotrange
	YvalsA = np.array(YvalsA) * plotrange[1]
	YvalsB = np.array(YvalsB) * plotrange[1]

	# From the list of datafiles, read data and use bokeh to generate javascript plots, then create html with bokeh's plots.
	for datafile in datafileslist:											# for each data file
		print 'datafile used: {0}\n'.format(os.path.split(datafile)[1])		# print the name of the current data file 

		ds = DataStruct(datafile, 											# create new DataStruct instance
		A_code = A_code, B_code = B_code, trial_code = trial_code,			# codes for percepts and trial
		epsilon = epsilon, plotrange = plotrange, shiftval = shiftval)		# other parameters

		mycontainer = [html_container() for k in range(ds.numtrials + 2)] 	# container for html and javascript plot codes
		cit = 0 															# container iterator

		Tmax = ds.trial_ts[-1] + 3000										# get ending time of last trial

	
		# Plot input only (not used now) ------------------------------------------------------------------------------------------------------
		if not ds.eyetrackerdata:
	
			bokehfig = figure(title = 'Input time stamps')
			plot = bokeh_plotTC(bokehfig, ds.A_ts, Tmax, YvalsA, A_color, change_axis=1, label = 'Left input')		# plot TC. left press
			plot = bokeh_plotTC(bokehfig, ds.B_ts, Tmax, YvalsB, B_color, change_axis=1, label = 'Right input')		# plot TC. left press
			
			bokehfig.xaxis.axis_label='Time (ms)'

			mycontainer[cit].scriptX, mycontainer[cit].divX = components(plot, CDN) # add javascript cdode generated by bokeh to container

		else:

			# Plot X and Y gaze data over time stamps of all experiment ---------------------------------------------------------------------------
			# Plot X coordinate for both eyes -----------------------------------------------------------------------------------------------------

			bokehfig = figure(title = 'X coordinates. Right eye shifted {0}'.format(shiftval))

			bokehfig.scatter(ds.timestamps,ds.leftgazeX,  marker = 'x', color=rgb2hex(A_color), legend='left eye')
			bokehfig.scatter(ds.timestamps,ds.rightgazeX, marker = 'o', color=rgb2hex(B_color), legend='right eye')

			for event in ds.trial_ts:																			# for each event time stamp
			 	bokehfig.line((event, event), (plotrange[0],plotrange[1]), 'k-', color = rgb2hex((0,0,0)))		# plot a vertical line: plt.plot((x1,x2),(y1,y2),'k-')

			plot = bokeh_plotTC(bokehfig, ds.A_ts, Tmax, YvalsA, A_color, change_axis=1, label = 'Left input')	# plot TC. left press
			plot = bokeh_plotTC(bokehfig, ds.B_ts, Tmax, YvalsB, B_color, change_axis=1, label = 'Right input')	# plot TC. left press
			
			bokehfig.xaxis.axis_label='Time (ms)'
			bokehfig.yaxis.axis_label='X gaze'

			# samples = 5
			# LGavg = movingaverage(ds.leftgazeX[idx_start:idx_end], samples)
			# TSavg = movingaverage(ds.timestamps[idx_start:idx_end], samples)
			# # print LGavg

			# bokehfig.line(TSavg, LGavg, size=12, color="red", alpha=0.5)

			mycontainer[cit].scriptX, mycontainer[cit].divX = components(plot, CDN) # add javascript cdode generated by bokeh to container

			## plot Y coordinate for both eyes -----------------------------------------------------------------------------------------------------

			bokehfig = figure(title = 'Y coordinates. Right eye shifted {0}'.format(shiftval))
			
			bokehfig.scatter(ds.timestamps,ds.leftgazeY,  marker = 'x', color=rgb2hex(A_color), legend='left eye')
			bokehfig.scatter(ds.timestamps,ds.rightgazeY, marker = 'o', color=rgb2hex(B_color), legend='right eye')

			for event in ds.trial_ts:																			# for each event time stamp
			 	bokehfig.line((event, event), (plotrange[0],plotrange[1]), 'k-', color = rgb2hex((0,0,0)))		# plot a vertical line: plt.plot((x1,x2),(y1,y2),'k-')

			plot = bokeh_plotTC(bokehfig, ds.A_ts, Tmax, YvalsA, A_color, change_axis=1, label = 'Left input')		# plot TC. left press
			plot = bokeh_plotTC(bokehfig, ds.B_ts, Tmax, YvalsB, B_color, change_axis=1, label = 'Right input')	# plot TC. left press
			
			bokehfig.xaxis.axis_label='Time (ms)'
			bokehfig.yaxis.axis_label='Y gaze'

			mycontainer[cit].scriptY, mycontainer[cit].divY = components(plot, CDN) # add javascript cdode generated by bokeh to container
			cit += 1


			# For each trial, plot gaze and input ----------------------------------------------------------------------------------------------------
			if ds.numtrials > 1:
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

					trial_ts = [start, end] 										# 

					ts  = ds.timestamps[idx_start:idx_end] 							# timestamps   of this trial
					lgX = ds.leftgazeX[idx_start:idx_end] 							# left  X gaze of this trial
					lgY = ds.leftgazeY[idx_start:idx_end] 							# left  Y gaze of this trial
					rgX = ds.rightgazeX[idx_start:idx_end]							# right X gaze of this trial
					rgY = ds.rightgazeY[idx_start:idx_end] 							# right Y gaze of this trial

					## plot X coordinate for both eyes -----------------------------------------------------------------------------------------------------

					bokehfig = figure(title = 'Trial {0}. X coordinate. Right eye shifted {1}'.format(trial+1,shiftval))
					
					bokehfig.scatter(ts,lgX,  marker = 'x', color=rgb2hex(A_color), legend='left eye')
					bokehfig.scatter(ts,rgX,  marker = 'o', color=rgb2hex(B_color), legend='right eye')

					for event in trial_ts:																				# for each event time stamp
					 	bokehfig.line((event, event), (plotrange[0],plotrange[1]), 'k-', color = rgb2hex((0,0,0)))		# plot a vertical line: plt.plot((x1,x2),(y1,y2),'k-')

					plot = bokeh_plotTC(bokehfig, ds.A_trial[trial], Tmax, YvalsA, A_color, change_axis=1, label = 'Left input')		# plot TC. left press
					plot = bokeh_plotTC(bokehfig, ds.B_trial[trial], Tmax, YvalsB, B_color, change_axis=1, label = 'Right input')		# plot TC. left press
					
					bokehfig.xaxis.axis_label='Time (ms)'
					bokehfig.yaxis.axis_label='X gaze'


					mycontainer[cit].scriptX, mycontainer[cit].divX = components(plot, CDN) # add javascript cdode generated by bokeh to container
					
					## plot Y coordinate for both eyes -----------------------------------------------------------------------------------------------------
					
					bokehfig = figure(title = 'Trial {0}. Y coordinate. Right eye shifted {1}'.format(trial+1,shiftval))
					
					bokehfig.scatter(ts, lgY,  marker = 'x', color=rgb2hex(A_color), legend='left eye')
					bokehfig.scatter(ts, rgY,  marker = 'o', color=rgb2hex(B_color), legend='right eye')

					for event in trial_ts:																				# for each event time stamp
					 	bokehfig.line((event, event), (plotrange[0],plotrange[1]), 'k-', color = rgb2hex((0,0,0)))		# plot a vertical line: plt.plot((x1,x2),(y1,y2),'k-')

					plot = bokeh_plotTC(bokehfig, ds.A_trial[trial], Tmax, YvalsA, A_color, change_axis=1, label = 'Left input')		# plot TC. left press
					plot = bokeh_plotTC(bokehfig, ds.B_trial[trial], Tmax, YvalsB, B_color, change_axis=1, label = 'Right input')		# plot TC. left press
					
					bokehfig.xaxis.axis_label='Time (ms)'
					bokehfig.yaxis.axis_label='Y gaze'

					mycontainer[cit].scriptY, mycontainer[cit].divY = components(plot, CDN) # add javascript cdode generated by bokeh to container
					

					# Optional: Create X,Y video for current trial ------------------------------------------------------------------------
					if createvideoYN and trial in videofortrials: 
						print 'create video for trial {0}'.format(trial)
						videoname = '{0}_{1}_Trial_{2}_XYplotmoviepy.mp4'.format(ds.expname, ds.subjectname, trial+1)

						# filter data per 5
						samples = 100
						ts  = movingaverage(ds.timestamps[idx_start:idx_end], samples)
						lgx = movingaverage(ds.leftgazeX[idx_start:idx_end],samples)
						lgy = movingaverage(ds.leftgazeY[idx_start:idx_end],samples)

						t = time.time()
						createvideowithmoviepy(ts, lgx, lgy, videoname = videoname)
						elapsed = time.time() - t
						print 'creating a video with matplotlib took: {0} seconds'.format(elapsed)

						mycontainer[cit].XYvideolink = videoname

					# Optional: Create High-angle video for current trial ------------------------------------------------------------------------
					if create_highangle_videoYN and trial in videofortrials:
						videoname = '{0}_{1}_Trial_{2}_HAplot.mp4'.format(ds.expname, ds.subjectname, trial+1)
						print 'creating high angle video'
						create_highangle_video(ds.timestamps[idx_start:idx_end], ds.leftgazeX[idx_start:idx_end], ds.rightgazeX[idx_start:idx_end], videoname = 'highanglevideo.mp4')

						mycontainer[cit].HAvideolink = videoname
						
					cit += 1
					it += 2 																					# increase iterator


		# Create Interactive html ------------------------------------------------------------------------------------------------------------
		fWebName = '{0}.html'.format(os.path.splitext(os.path.split(datafile)[1])[0])
		## copy header
		with open(fWeb_HEADER,'r') as head:
			header = head.read()

		with open(fWebName, 'w' ) as fWebID:															#
			fWebID.seek(0)
			create_interactive_html(datastruct = ds, cont = mycontainer, fWebID=fWebID, fWeb_HEADER = header)

		print 'html saved as {0}'.format(fWebName)


		# Create html --------------------------------------------------------------------------------------------------------------------------
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

class DataStruct():
	def __init__(self, datafile, A_code = 1, B_code = 4, trial_code = 8, epsilon = 0.0123, plotrange = [-1.1,1.1], shiftval = 0.0):
		
		self.filenamefp 	= datafile 		# full path of data file
		self.filename 		= '' 			# data filename 
		self.eyetrackerdata = False 		# True if et data, False if just input
		self.numtrials 		= 0				# number of trials in data file

		# eyetracker data
		self.timestamps 	= []			# eyetracker time stamps
		self.leftgazeX  	= []			# 
		self.leftgazeY  	= []			# 
		self.rightgazeX 	= []			# 
		self.rightgazeY 	= []			# 
		self.leftvalidity 	= []			#
		self.rightvalidity 	= []			#


		self.trial_ts 	= [] 				# time stamps for trials

		# percept data
		self.A_trial 	= [] 				# time stamps for A in trial
		self.B_trial 	= [] 				# time stamps for B in trial
		self.A_ts 	 	= [] 				# time stamps for A
		self.B_ts    	= [] 				# time stamps for B

		# constants
		self.A_code 	= A_code 			# code value for A percept
		self.B_code 	= B_code 			# code value for B percept
		self.trial_code = trial_code 		# code value for trials
		self.epsilon 	= epsilon 			# epsilon
		self.plotrange 	= plotrange 		# plotrange 
		self.shiftval 	= shiftval 			# value to shift Y

		self.read_data()					# read data

		self.expname = ''
		self.subjectname = ''

		pass

	def read_data(self):
		# Read data file --------------------------------------------------------------------------------------------
		self.filename = os.path.split(self.filenamefp)[1] 										# get just data file name, not full path
		try:
			data = np.genfromtxt(self.filenamefp, delimiter="\t", dtype=None, names=True)		# read data file
		except ValueError:
			print 'cannot read data file'
			sys.exit()

		# Determine if datafile contains eyetracker data or just input (mouse) ----------------------------------------
		et_data = True if 'LeftGazePoint2Dx' in data.dtype.names else False						# if LeftGazePoint2Dx in header, et_data is True, else is False

		
		# Read events data --------------------------------------------------------------------------------------------

		ets 	  = data['EventTimeStamp'][data['EventTimeStamp']!='-'].astype(np.float) 		# event time stamp: filter out values with '-' and convert str to float
		ecode	  = data['Code'][data['Code'] != '-'].astype(np.float)							# event code: filter out values with '-' and convert to float

		Trial_on  = ets[ecode ==  self.trial_code] 												# get timestamp of trials start
		Trial_off = ets[ecode == -self.trial_code] 												# get timestamp of trials end

		A_on  	  = ets[ecode ==  self.A_code] 													# get timestamp of percept A on (LEFT press)
		A_off 	  = ets[ecode == -self.A_code] 													# get timestamp of percept A off (LEFT release)

		B_on  	  = ets[ecode ==  self.B_code] 													# get timestamp of percept B on (RIGHT press)
		B_off 	  = ets[ecode == -self.B_code] 													# get timestamp of percept B off (RIGHT release)

		self.numtrials = len(Trial_on) 															# compute number of trials

		# datastruct
		self.trial_ts = np.empty((Trial_on.size + Trial_off.size,), dtype=Trial_on.dtype) 		# create empty matrix of specific lenght
		self.trial_ts[0::2] = Trial_on 															# put Trial_on on even spaces 
		self.trial_ts[1::2] = Trial_off 														# put Trial_off on odd spaces

		# Check input events --------------------------------------------------------------------------------------------

		# Get input in each trial
		x, y, z = 2, 0, self.numtrials 															# size of percept matrix
		self.A_trial = [[[0 for k in xrange(x)] for j in xrange(y)] for i in xrange(z)]			# matrix for A percept of each trial
		self.B_trial = [[[0 for k in xrange(x)] for j in xrange(y)] for i in xrange(z)]			# matrix for B percept of each trial

		it = 0 																					# iterator
		for trial in range(self.numtrials): 													# for each trial
			start = self.trial_ts[it]															# timestamp start of trial
			end   = self.trial_ts[it+1]															# timestamp end of trial

			A_on_in_trial = [i for i in A_on if start<i<end]									# get A_on in trial

			for ts_on in A_on_in_trial:															# for each A_on
				val, idx_start = find_nearest_above(A_off, ts_on)								# look for the nearest above A_off
				
				if val is not None:																# compare nearest above to end of trial,
					ts_off = np.minimum(end,val) 												# get minimum												
				else:
					ts_off = end

				self.A_trial[trial].append([ts_on, ts_off]) 									# add A_on and A_off times to percept matrix

			B_on_in_trial = [i for i in B_on if start<i<end]									# get A_on in trial

			for ts_on in B_on_in_trial:															# for each B_on
				val, idx_start = find_nearest_above(B_off, ts_on)								# look for the nearest above B_off
				
				if val is not None: 															# compare nearest above to end of trial,
					ts_off = np.minimum(end,val)												# get minimum
				else:
					ts_off = end

				self.B_trial[trial].append([ts_on, ts_off])										# add B_on and B_off times to percept matrix

			it += 2 																			# increase iterator

			for item in self.A_trial[trial]:               										# datastruct.A/B_ts will contain on and off
				self.A_ts.append(item) 															# time staps in the following way:
			for item in self.B_trial[trial]: 													# [[on_1, off_2], [on_2, off_2] ...]
				self.B_ts.append(item) 															# 

		# Read eyetracker data ---------------------------------------------------------------------------------------
		if et_data:
			self.eyetrackerdata = True 															# indicate that datastruct contains eyetracker data

			self.timestamps 	= np.array(map(float, data['Timestamp']))						# get time stamps of the eye tracker data

			self.leftgazeX 		= np.array(map(float, data['LeftGazePoint2Dx']))				# get left gaze X data
			self.leftgazeY 		= np.array(map(float, data['LeftGazePoint2Dy']))				# get left gaze Y data
			self.leftvalidity 	= np.array(map(float, data['LeftValidity']))					# get left gaze validity
			
			self.rightgazeX 	= np.array(map(float, data['RightGazePoint2Dx']))				# get right gaze X data
			self.rightgazeY 	= np.array(map(float, data['RightGazePoint2Dy']))				# get right gaze Y data
			self.rightvalidity 	= np.array(map(float, data['RightValidity']))					# get right gaze validity

			# Tobii gives data from 0 to 1, we want it from -1 to 1:
			self.leftgazeX 		= 2 * self.leftgazeX 	- 1
			self.leftgazeY 		= 2 * self.leftgazeY 	- 1
			self.rightgazeX 	= 2 * self.rightgazeX - 1
			self.rightgazeY 	= 2 * self.rightgazeY - 1

			# Map values outside of range to the boundaries
			self.leftgazeX[self.plotrange[0]  > self.leftgazeX]  = self.plotrange[0]; self.leftgazeX[self.plotrange[1] < self.leftgazeX] = self.plotrange[1]
			self.leftgazeY[self.plotrange[0]  > self.leftgazeY]  = self.plotrange[0]-self.shiftval; self.leftgazeY[self.plotrange[1] < self.leftgazeY] = self.plotrange[1]-self.shiftval
			self.rightgazeX[self.plotrange[0] > self.rightgazeX] = self.plotrange[0]; self.rightgazeX[self.plotrange[1] < self.rightgazeX] = self.plotrange[1]
			self.rightgazeY[self.plotrange[0] > self.rightgazeY] = self.plotrange[0]; self.rightgazeY[self.plotrange[1] < self.rightgazeY] = self.plotrange[1]

			# compute percentage of validity
			self.dataloss = []
			
			it = 0
			for trial in range(self.numtrials): 												# for each trial
				start = self.trial_ts[it]														# timestamp start of trial
				end   = self.trial_ts[it+1]														# timestamp end of trial

				# get row index
				val, idx_start = find_nearest_above(self.timestamps, start)
				val, idx_end   = find_nearest_above(self.timestamps, end)

				nsamples = idx_end - idx_start

				lv_trial = 100 * (self.leftvalidity[idx_start:idx_end] == 4).sum()/float(nsamples) 	# left eye:  % of lost data
				rv_trial = 100 * (self.rightvalidity[idx_start:idx_end] == 4).sum()/float(nsamples)	# right eye: % of lost data

				self.dataloss.append([lv_trial, rv_trial])

				print 'For trial {0}, {1} % of data was lost'.format(trial+1, "%.1f" % lv_trial)	# (e.g. validity equal to 4)

				it += 1 
			# sys.exit()

class html_container():
	def __init__(self):
		self.scriptX = []		# javascript code for X gaze bokeh's plot
		self.divX 	 = []		# html div that references self.scriptX

		self.scriptY = []		# javascript code for Y gaze bokeh's plot
		self.divY 	 = []		# html div that references self.scriptX

		self.hist_script = []	# javascript code for histogram bokeh's plot
		self.hist_div	 = []	# html div that references self.hist_script

		self.XYvideolink = []	# relative path to the x,y gaze video
		self.HAvideolink = []	# relative path to the high angle video


	def function(self):
		pass

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

	return figure

def bokeh_histogram(figure, percept_timestamps, binw, fil_color = "#036564", line_color="#033649"):
	# 	Create a histogram:
	# - figure: 			bokeh figure
	# - percept_timestamps: list of lists containing percept time values as [[on_0 off_0] [on_1 off_1] ... ]
	# - binw: 				number of bins for the histogram
	percept_duration = [x[1] - x[0] for x in percept_timestamps]													# compute duration of each percept
	hist, edges = np.histogram(percept_duration, density=True, bins=binw) 											# create histogram
	figure.quad(top=histA, bottom=0, left=edges[:-1], right=edges[1:], fill_color=fil_color, line_color=line_color) # plot histogram

	return figure	

def rgb2hex(color):

	if max(color) <= 1:
		color = (np.array(color) * 255).astype(int).tolist()
	
	r = max(0, min(color[0] , 255))
	g = max(0, min(color[1] , 255))
	b = max(0, min(color[2] , 255))

	return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)

def create_interactive_html(datastruct = None, cont = None, fWebID='', fWeb_HEADER = ''):
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

if __name__ == '__main__':

	if len(sys.argv) < 2:
		print 'Choose which data files to analyze'
	else:
		pass
	
	## Create GUI to open files
	Tk().withdraw() 													# we don't want a full GUI, so keep the root window from appearing
	datafileslist = askopenfilenames(title='Chose files to analyze') 	# show an "Open" dialog box and return the path to the selected file

	# datafileslist = ['C:/Users/NuEye/Google Drive/NuEyeUPF/RubinLabs_Experiments/Experiment01 - Plaid/data/Plaid_v19-15.03.09_17.28_JL1_newdata_eyet.txt']
	main(datafileslist = datafileslist, fWeb_HEADER = 'html_template.html')