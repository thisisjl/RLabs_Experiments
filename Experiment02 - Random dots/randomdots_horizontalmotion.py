import os, sys

lib_path = os.path.abspath(os.path.join('..','_Libraries'))
sys.path.append(lib_path)

from rlabs_libutils import *
from rlabs_libtobii import EyetrackerBrowser, MyTobiiController             			# this is OUR library for the tobii eyetracker

from pyglet.window import Window, mouse
from pyglet.gl import *                                                     			# to change the color of the background
from pyglet import clock
import time
import numpy as np


def main(num_dots=100, Tau = 100, haveeyetracker = 0):
	
	screens = pyglet.window.get_platform().get_default_display().get_screens()			# get number of screens
	win = MyWindow(fullscreen = True, screen = screens[0], visible = 0)					# create window
	center = win.width/2, win.height/2 													#
	fg_color = (0,0,0) 																	#
	clockDisplay = clock.ClockDisplay(color=(1,1,1,1))                      			# to display frames per second
	framerate = 60.0 																	#
	clock.set_fps_limit(framerate)                                          			# set limit for frames per second

	frameMs = 1.0/framerate                                        						# manual frame rate control: frameMs is the time in ms a frame will be displayed

	parameters = []
	speed = 500 																		# pixels per second
	
	# define limits
	liml, limr = win.width/4, win.width - win.width/4 									#
	cyclestart, cycleend = liml, limr 													#

	# compute dots position: liml < x < limr
	x = np.random.rand(num_dots) * (cycleend - cyclestart) + cyclestart					#
	y = np.random.rand(num_dots) * win.height 											#
	z_fb = 2 * np.mod(np.random.permutation(num_dots),2) - 1 							#

	vertices = np.empty((x.size + y.size,), dtype=x.dtype)               				# create empty array to allocate x and y coordinates
	age = np.random.randint(Tau, size=num_dots) 										#
	age[0] = 10000
	# compute distance between x and cyclestart
	dxcys = (x - liml) - cyclestart 													#
	cycle = cycleend - cyclestart 														#
	
	dx = np.empty(z_fb.size) 															#

	
	# handling events ---------------------------------------------------------------------------------------------------  
	events_struct = []                                                      			# list that contains event that the event handler sends.
	eventcount = 0                                                          			# counter of the events

	events_handler = {                                                      			# events handler (it needs to be set to window)
	    'on_mouse_press'    : lambda e: events_struct.append(e),            			# append on_mouse_press event to events_struct
	    'on_mouse_release'  : lambda e: events_struct.append(e),}           			# append on_mouse_release event to events_struct

	events_handler_with_ET = {                                                                              # if using eyetracker, this will add
	    'on_mouse_press'    : lambda e: (events_struct.append(e), controller.myRecordEvent2(event = e)),    # to events_struct and also it will 
	    'on_mouse_release'  : lambda e: (events_struct.append(e), controller.myRecordEvent2(event = e)),}   # call MyRecordEvent2 with the event


    # prepare for eyetracker ----------------------------------------------------------------------------------------------
	if haveeyetracker:
		if not os.path.isdir('data'):                                           				# if there is not a folder called 'data',
		    os.makedirs('data')                                                 				# create it
		eyetrackeroutput   = os.path.join('data',("Randomdots" + "-" + time.strftime( 			# eyetracker data file name
			"%y.%m.%d_%H.%M", time.localtime()) + "_" + subjectname + "_" + "eyet" + ".txt"))	#
		eb = EyetrackerBrowser()																# Create an EyetrackerBrowser
		eb.main()																				# display EyetrackerBrowser

		controller = MyTobiiController( 														# create Tobii controller
			datafilename=eyetrackeroutput, 														# pass it data file name
			parameters=parameters)       														# pass it parameters
		controller.waitForFindEyeTracker()                                  					# wait to find eyetracker
		controller.activate(controller.eyetrackers.keys()[0])               					# activate eyetracker

		controller.startTracking()                                                              # start the eye tracking recording
		time.sleep(0.2)                                                                         # wait for the eytracker to warm up
		controller.myRecordEvent2(EventItem(name = 'TrialEvent', counter = 0, 
			timestamp = time.time(), etype = 0, eid = 'START'))

		win.events_handler = events_handler_with_ET                       						# set window events_handler with eye tracker
	else:
		win.events_handler = events_handler                               						# set window events_handler

	
	# Stimulus loop  -------------------------------------------------------------------------------------------------------------
	win.set_visible(True) 																#
	win.set_mouse_visible(False)                                          				# set mouse to not visible
	timestart = time.time() 															#
	while not win.has_exit:
		glClearColor(fg_color[0],fg_color[1],fg_color[2],1)                 			# set background color
		win.clear()                                                         			# clear window
		win.dispatch_events()                                               			# dispatch window events (very important call)
		timenow = time.time() 															# get time of iteration
		
		# Check if dots are dead ------------------------------------------------------------------------------------------------
		newdots  = (age == 0) 															#
		x[newdots]    = np.random.rand(np.sum(newdots)) * (cycleend - cyclestart) + cyclestart           			#
		y[newdots]    = np.random.rand(np.sum(newdots)) * win.height 					#

		# update position --------------------------------------------------------------------------------------------------------
		dividend       = x + z_fb * (speed * (timenow - timestart))  					#
		dx[z_fb == 1]  = np.fmod(dividend[z_fb == 1], cycle) + cyclestart 							#
		dx[z_fb == -1] = cycleend - np.fmod(cycleend - dividend[z_fb == -1], cycle) 	#
		dotxpos        = dx 															#

		# Update ages -------------------------------------------------------------------------------------------------------------
		age          = age - 1 															#
		age[age==-1] = Tau - 1  														# 
		
		# Draw dots ---------------------------------------------------------------------------------------------------------------
		vertices[0::2] = dotxpos														# x coords will be in even indices
		vertices[1::2] = y																# y coords will be in odd indices
		drawpoints(vertices, color = (255,255,255), size = 5)  							# draw dots

		clock.tick() 																	#
		clockDisplay.draw()                                                 			# display frames per second
		win.flip()                                                          			# flip window
		
		# manual frame control ----------------------------------------------------------------------------------------------------
		endMs = time.time() 															# manual frame rate control: time point when frame ends.
		delaytime = frameMs - (endMs - timenow) 										# manual frame rate control: time time frame must be frozen.
		if delaytime > 0: time.sleep(delaytime)											# manual frame rate control: freeze frame


	if haveeyetracker:																	# Stop eyetracker processes
		controller.myRecordEvent2(EventItem(name = 'TrialEvent', counter = 1, 
			timestamp = time.time(), etype = 0, eid = 'END'))
		controller.stopTracking()                                           			# stop eye tracking and write output file
		controller.destroy()                                                			# destroy controller

if __name__ == '__main__':
    main()