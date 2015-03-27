import os, sys

lib_path = os.path.abspath(os.path.join('..','_Libraries'))
sys.path.append(lib_path)

from rlabs_libtobii import EyetrackerBrowser, MyTobiiController             # this is OUR library for the tobii eyetracker
from rlabs_libutils import MyWindow, drawpoints, EventItem

from pyglet.gl import *                                                     # to change the color of the background
from pyglet import clock

import numpy as np
import time
from collections import OrderedDict

def main(Tau = 100, CycleDur = 360, num_dots = 1, zDir = 1, TranspYN = 1, subjectname = 'None', testing_with_eyetracker = 1):
	"""
	Usage: RDK_uniformXY(Tau,CycleDur,NumDots,zDir,TranspYN)
		Tau: dot lifetime in frames 
	        [default: 15]
		CycleDur: duration of one sphere revolve, in frames 
	        [default: 360   <--> rotation of 1deg/frame]
		NumDots: total # points on front surface (note, will be << for Transp=N)
	        [default: 1000]
		zDir, direction of rotation about z-axis: 1 (front-surf to right) or -1
	        [default: 1; note: meaningful only if Transp=Y]
		TranspYN: transparent sphere if 1, opaque spehre if 0
	        [default: 1]
		subjectname: to name the output data of the eyetracker
			[default: None]
		testing_with_eyetracker: 1 if using eyetracker, 0 if not
			[default: 0]
	"""
	## initialize window
	screens = pyglet.window.get_platform().get_default_display().get_screens()					# get number of screens
	win = MyWindow(fullscreen = True, screen = screens[0], visible = 0)							# create window
	center = win.width/2, win.height/2 															# compute center
	clockDisplay = clock.ClockDisplay(color=(1,1,1,1))											# to display frames per second
	framerate = 60.0
	clock.set_fps_limit(framerate)                                          					# set limit for frames per second
	fg_color = np.array([0.5, 0.5, 0.5])

	## random dots parameters
	color 		= (255,255,255)																	# color of dots
	size_dot 	= 2 																			# size of the dots
	fix_color 	= (0,0,0) 																		# color of fixation point
	fix_size 	= 10  																			# size of fixation point

	## Compute parameters
	R = win.height/2 #300 																		# radius of sphere
	dOmega = 2 * np.pi / CycleDur 																# angular rotation per frame

	parameters = OrderedDict(('number of dots',num_dots),('dot color',color), 					# create parameters dict
		('dot size',size_dot), ('fixation point color',fix_color), 								# to pass to eyetracker
		('fixation point size',fix_size),('fixation point size',fix_size),('sphere radius',R),
		('dOmega',dOmega),('max dot lifetime',Tau),('Cycle duration',CycleDur),
		('direction of rotation',zDir),('transparentYN',TranspYN),('subject name',subjectname),
		('eyetracker',testing_with_eyetracker))

	# uniformly distribute random dots on XY plane (regradless of shape)
	x 	 = 2 * R * np.random.rand(num_dots) - R													# distribute dots between [-R,R]
	y 	 = 2 * R * np.random.rand(num_dots) - R													# distribute dots between [-R,R]
	z_fb = 2 * np.mod(np.random.permutation(num_dots),2) - 1									# binary: front (1) or back (-1)
	xmax = np.sqrt(R * R - y * y)																# rotation radius of dots on sphere's surface
	age  = np.mod(np.random.permutation(num_dots), Tau) 										# initial dot's age: uniform between 0 and Tau-1

	## modify parameters of last dot, which will be the fixation point
	TMAX             = 10000																	# infinite lifetime is TMAX frames
	age[num_dots-1]  = TMAX																		# give last dot infinite lifetime
	x[num_dots-1]    = 0#center[0] 																# put dot in center of screen
	y[num_dots-1]    = 10#center[1] 															# put dot in center of screen
	z_fb[num_dots-1] = 1.0		 																# put dot in front (initially)
	xmax[num_dots-1] = R																		# xmax is radius


  	## draw first frame

	# # interweave xpos and ypos
	# vertices = np.empty((x.size + y.size,), dtype=x.dtype) 										# create empty array to allocate x and y coordinates
	# vertices[0::2] = x 																			# x coords will be in even indices
	# vertices[1::2] = y 	 																		# y coords will be in odd indices

	# # while not win.has_exit:
	# # 	win.dispatch_events() 																	# dispatch window events (essential)
	# # 	win.clear()																				# clear window

	# # 	drawpoints(vertices, color = color, size = size_dot)									# draw points
	# # 	clockDisplay.draw() 																	# display frames per second

	# # 	win.flip()

	# # sys.exit()

	if testing_with_eyetracker:
		# data files name:
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
		controller.myRecordEvent2(EventItem(name = 'TrialEvent', counter = 0, timestamp = time.time(), etype = '{0} START'.format(0), eid = time.time()))
   


	## Stimuli loop -----------------------------------------------------------------------------------------------------------------
	win.set_visible(True)
	while not win.has_exit:
		glClearColor(fg_color[0],fg_color[1],fg_color[2],1)             						# set background color
		win.dispatch_events() 																	# dispatch window events (essential)
		win.clear()																				# clear window

		## reposition surviving dots
		indots  = ((x * x + y * y) < (R * R)) 													# move only the dots that fall within target shape
		indots[-1] = True
		livdot = ((age > 0) & indots) 															# surviving out-dots will be left unchanged


		## before projection on XY plane:
		#	cylinder: all dots rotate at V = R * omega, regardless of y
		#	sphere: dots rotate at V = xmax * omega, with xmax = sqrt(R^2-y^2)
		# projected on XY plane:
		#	Vprojected = z_fb * V * (sqrt(R^2-x^2)/R)

		dx    = np.empty(x.size) 																# allocate space
		dx[:] = np.NAN 																			# create NotANumber array
		dx[livdot] = dOmega * z_fb[livdot] * xmax[livdot] * (np.sqrt(R * R - x[livdot] * x[livdot]) / R) # projected coordinates

		xnew    = np.empty(x.size) 																# allocate space
		xnew[:] = np.NAN 																		# create NotANumber array

		xnew[livdot] = x[livdot] + dx[livdot] 													# update position

		# if xnew fell outside of sphere, correct +flip rotation dir for  next iterations
		flipz = (np.abs(xnew) > xmax) & livdot

		xnew[flipz] = 2 * z_fb[flipz] * xmax[flipz] - xnew[flipz] 								# = xmax - delta, where delta = xnew - xmax
		z_fb[flipz] = - z_fb[flipz]

		# update positions
		x[livdot] = xnew[livdot]

		# replace end-of-life dots
		newdots 	  = (age == 0)
		x[newdots] 	  = np.random.rand(np.sum(newdots))
		x[newdots]	  = 2 * R * x[newdots] - R
		y[newdots]	  = np.random.rand(np.sum(newdots))
		y[newdots]	  = 2 * R * y[newdots] - R

		z_fb[newdots] = 2 * np.mod(np.random.permutation(np.sum(newdots)),2) - 1
		xmax[newdots] = np.sqrt(R * R - y[newdots] * y[newdots])

		# update ages
		age 		 = age - 1
		age[age==-1] = Tau - 1
	
		# draw points
		if TranspYN: 																			# sphere is transparent
			# interweave x and y coordinates
			xpos = x[z_fb==1] + center[0] 														# center the points
			ypos = y[z_fb==1] + center[1] 														# in the middle of screen

			vertices = np.empty((xpos.size + ypos.size,), dtype=x.dtype) 						# create empty array to allocate x and y coordinates
			vertices[0::2] = xpos																# x coords will be in even indices
			vertices[1::2] = ypos																# y coords will be in odd indices
			drawpoints(vertices, color = color, size = size_dot)								# draw points

			# interweave xpos and ypos
			xpos = x[z_fb==-1] + center[0] 														# center the points
			ypos = y[z_fb==-1] + center[1] 														# in the middle of the screen

			vertices = np.empty((xpos.size + ypos.size,), dtype=x.dtype)						# create empty array to allocate x and y coordinates
			vertices[0::2] = xpos																# x coords will be in even indices
			vertices[1::2] = ypos																# y coords will be in odd indices
			drawpoints(vertices, color = color, size = size_dot/2)								# draw points

			# draw fixation point in a different color and size:
			vertices = [x[-1]+center[0], y[-1]+center[1]] 										# fixation point is last in arrays
			drawpoints(vertices, color = fix_color, size = fix_size)							# draw point


		else:
			# interweave xpos and ypos
			xpos = x[z_fb==1] + center[0] 														# center the points
			ypos = y[z_fb==1] + center[1] 														# in the middle of the screen

			vertices = np.empty((xpos.size + ypos.size,), dtype=x.dtype) 						# create empty array to allocate x and y coordinates
			vertices[0::2] = xpos																# x coords will be in even indices
			vertices[1::2] = ypos																# y coords will be in odd indices

			drawpoints(vertices, color = color, size = size_dot)								# draw points

			# draw fixation point in a different color and size:
			vertices = [x[-1]+center[0], y[-1]+center[1]] 										# fixation point is last in arrays
			drawpoints(vertices, color = fix_color, size = fix_size)							# draw point
		
		clock.tick()
		clockDisplay.draw() 																	# display frames per second

		win.flip() #--------------------------------------------------------------------------- # flip window (end of stimuli loop)

	if testing_with_eyetracker:																	# Stop eyetracker processes
		controller.myRecordEvent2(EventItem(name = 'TrialEvent', counter = 1, timestamp = time.time(), etype = '{0} END'.format(0), eid = time.time()))
		controller.stopTracking()                                           					# stop eye tracking and write output file
		controller.destroy()                                                					# destroy controller


if __name__ == '__main__':

    print 'running RDK'

    if len(sys.argv) > 1:                           # optional: add a subject name
        subjectname = sys.argv[1]                   # run as python Plaid_v19 subjectname
    else:
        subjectname = 'defaultsubjectname'			# if not, a default will be used

    main(subjectname = subjectname)
    
