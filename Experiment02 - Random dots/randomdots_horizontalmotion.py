import os, sys

lib_path = os.path.abspath(os.path.join('../..','_Libraries'))
sys.path.append(lib_path)

from rlabs_libutils import *

from pyglet.window import Window, mouse
from pyglet.gl import *                                                     			# to change the color of the background
from pyglet import clock
import time
import numpy as np


def main(num_dots=100, Tau = 100):
	win = MyWindow(fullscreen = True)
	center = win.width/2, win.height/2
	fg_color = (0,0,0)
	clockDisplay = clock.ClockDisplay(color=(1,1,1,1))                      			# to display frames per second
	framerate = 60.0
	clock.set_fps_limit(framerate)                                          			# set limit for frames per second

	speed = 500 																			# pixels per second
	motionpath = 1000 																	# maximum number of pixels each dot is going to move in its lifetime
	

	# define limits
	liml, limr = win.width/4, win.width - win.width/4
	cyclestart, cycleend = 0, win.width

	# compute dots position: liml < x < limr
	x    = np.random.rand(num_dots) * win.width#* (limr - liml) + liml
	y    = np.random.rand(num_dots) * win.height

	z_fb = 2 * np.mod(np.random.permutation(num_dots),2) - 1

	vertices = np.empty((x.size + y.size,), dtype=x.dtype)               				# create empty array to allocate x and y coordinates
	age = np.random.randint(Tau, size=num_dots)

	# compute distance between x and cyclestart
	dxcys = (x - liml) - cyclestart
	cycle = cycleend - cyclestart
	
	dx = np.empty(z_fb.size)

	# Stimulus loop  -------------------------------------------------------------------------------------------------------------
	timestart = time.time()
	while not win.has_exit:
		glClearColor(fg_color[0],fg_color[1],fg_color[2],1)                 			# set background color
		win.clear()                                                         			# clear window
		win.dispatch_events()                                               			# dispatch window events (very important call)
		timenow = time.time() 															# get time of iteration
		
		# Check if dots are dead ------------------------------------------------------------------------------------------------
		newdots  = (age == 0) 															#
		x[newdots]    = np.random.rand(np.sum(newdots)) * win.width           			#
		y[newdots]    = np.random.rand(np.sum(newdots)) * win.height 					#

		# update position --------------------------------------------------------------------------------------------------------
		dividend = x + z_fb * (speed * (timenow - timestart))
		dx[z_fb == 1] = np.fmod(dividend[z_fb == 1], cycle)
		dx[z_fb == -1] = cycleend - np.fmod(cycleend - dividend[z_fb == -1], cycle)
		dotxpos = dx

		# Update ages -------------------------------------------------------------------------------------------------------------
		age          = age - 1 															#
		age[age==-1] = Tau - 1  														# 

		# Draw dots ---------------------------------------------------------------------------------------------------------------
		vertices[0::2] = dotxpos														# x coords will be in even indices
		vertices[1::2] = y																# y coords will be in odd indices
		drawpoints(vertices, color = (255,255,255), size = 5)  							# draw dots

		clock.tick()
		clockDisplay.draw()                                                 			# display frames per second
		win.flip()                                                          			# flip window

if __name__ == '__main__':
    main()