import os, sys

lib_path = os.path.abspath(os.path.join('..','_Libraries'))
sys.path.append(lib_path)

from rlabs_libtobii import EyetrackerBrowser, MyTobiiController             # this is OUR library for the tobii eyetracker
from rlabs_libutils import *

from pyglet.window import Window
from pyglet.gl import *                                                     # to change the color of the background
from pyglet import clock

import time                                                                 # for the while loop
from numpy.random import permutation as np_permutation                      # for random trials

def main(ExpName = 'Plaid_v20', subjectname = ''):
    ######################################################
    ## Load parameters
    ######################################################
    if getattr(sys, 'frozen', False):                                       # path is different
        application_path = os.path.dirname(sys.executable)                  # if its an executable
    elif __file__:                                                          # or a Python script,
        application_path = os.path.dirname(__file__)                        # look for it

    # config_name = "config_file"                                             # Name of the config file
    # trials_name = "trials_file"                                             # Name of the trials file
    
    # config_name_full = os.path.join(application_path, config_name)  # Full path name of the config file
    # trials_name_full = os.path.join(application_path, trials_name)  # Full path name of the trials file

    from config_file import (aperture_color,numTheta,apertureDiv,               # import config parameters
        red_color, cyan_color, stereo1, stereo2, fixp_color, surrp_color, 
        time_fixp, framerate, FPsize, fg_color, aperture_switch, forced,aperture_radius,
        testing_with_eyetracker, randomize_trials, fixYN)

    from trials_file import (numtrials,mylambda1, duty_cycle1, orientation1,    # import trials parameters
        speed1, mylambda2, duty_cycle2, orientation2, speed2, timeCurrentTrial)

    if forced:                                                                  # read forced transitions file
        transfilename = 'datatestN_NR_5_trans.txt'
        # transfilename_full = os.path.join(application_path, transfilename)      # Full path name of the transition file
        # transTimeL, transTimeR = read_forced_transitions(transfilename)
        transTimeL, transTimeR = read_forced_transitions(transfilename=transfilename)
        timeRamp = 0.5
    else:
        deltaX1 = 0
        deltaX2 = 0

    ## randomize trials ?
    if randomize_trials:
        trials_array = np_permutation(numtrials) # goes from 0 to numtrials in random order
    else:
        trials_array = range(numtrials) # no random


    screens = pyglet.window.get_platform().get_default_display().get_screens()
    if aperture_switch:
        allowstencil = pyglet.gl.Config(stencil_size = 8,double_buffer=True)
        MyWin = MyWindow(config=allowstencil, fullscreen = True, screen = screens[0], visible = 0)
    else:
        MyWin = MyWindow(fullscreen = True, screen = screens[0], visible = 0)
    

    xcenter = MyWin.width/2
    ycenter = MyWin.height/2

    clock.set_fps_limit(framerate)                                          # set limit for frames per second
    frameMs = 1000.0/framerate                                              # manual frame rate control: frameMs is the time in ms a frame will be displayed
    
    ######################################################  
    ## Initialize variables for data file
    ######################################################
    
    # Name of the data files
    eyetrackeroutput   = os.path.join('data',("Plaid_v19" + "-" + time.strftime("%y.%m.%d_%H.%M", time.localtime()) + "_" + subjectname + "_" + "eyet" + ".txt"))
    filename_data      = os.path.join('data',("Plaid_v19" + "-" + time.strftime("%y.%m.%d_%H.%M", time.localtime()) + "_" + subjectname + "_" + "alldata" + ".txt"))

    right_keys  = [4, 109, 110, 106] # right click, M, N, J                 # array with ascii codes for right keys
    left_keys   = [1, 122, 120, 115] # left click, Z, X, S                  # array with ascii codes for left keys
    
    lastevent = LastEvent()                                                 # LastEvent() is defined in rlabs_libutils
    data_struct = DataStruct()                                              # DataStruct() is defined in rlabs_libutils
    events_struct = []
    eventcount = 0

    # 3.4 - Initialize text to be shown at startup (not whown right now)
    textInstruc = "Continually report the motion of the grating in front.\nPress the left mouse button for left-ward motion.\nPress the right mouse button for right-ward motion\n\nClick mouse-wheel to start"
    # Use the mouse buttons to indicate the direction of the plaid in front.\n\nClick mouse-wheel to start"
    # textInstruc = "Use the mouse buttons to indicate the direction of the plaid in front.\n\nClick mouse-wheel to start"
    lbl_instr = pyglet.text.Label(text=textInstruc, font_name=None, font_size=36, bold=False, italic=False, 
        color=(0, 0, 0, 255), x = 100, y = MyWin.height/1.5, width=1400, height=None, 
        anchor_x='left', anchor_y='baseline', halign='left', multiline=True, dpi=None, batch=None, group=None)

    textInstruc2 = "Click mouse-wheel for next trial"
    lbl_instr2 = pyglet.text.Label(text=textInstruc2, font_name=None, font_size=24, bold=False, italic=False, 
        color=(0, 0, 0, 255), x = MyWin.width/2 - 200, y = MyWin.height/2.4, width=1400, height=None, 
        anchor_x='left', anchor_y='baseline', halign='left', multiline=True, dpi=None, batch=None, group=None)


    if testing_with_eyetracker:
        ######################################################
        ## Create an EyetrackerBrowser and display it
        ###################################################### 
        eb = EyetrackerBrowser()
        eb.main()

        ######################################################  
        ## Initialize controller (MyTobiiController)
        ######################################################
        controller = MyTobiiController(datafilename=eyetrackeroutput)       # create controller
        controller.waitForFindEyeTracker()                                  # wait to find eyetracker
        controller.activate(controller.eyetrackers.keys()[0])               # activate eyetracker
    

    ######################################################  
    ## Start trials
    ######################################################

    if testing_with_eyetracker:
        controller.startTracking()                                          # start the eye tracking recording
        time.sleep(0.2)                                                     # wait for the eytracker to warm up

    MyWin.set_visible(True)                                                 # set window to visible
    MyWin.set_mouse_visible(False)                                          # set mouse to not visible
    timeStart_general = time.time()                                         # get general start time
    
    for trial_counter in range(numtrials):                                  # for each trial 

        ######################################################  
        ## Prepare variables before stimulus loop
        ######################################################
        
        trial = trials_array[trial_counter]

        apertRad_pix = MyWin.height / apertureDiv
        
        grating11 = Grating(MyWin, mycoords(0,0, MyWin).x + stereo1, mycoords(0,0, MyWin).y, red_color, orientation1[trial], mylambda1[trial], duty_cycle1, apertRad_pix, speed1)
        grating12 = Grating(MyWin, mycoords(0,0, MyWin).x - stereo1, mycoords(0,0, MyWin).y, cyan_color, orientation1[trial], mylambda1[trial], duty_cycle1, apertRad_pix, speed1)
        grating21 = Grating(MyWin, mycoords(0,0, MyWin).x + stereo2, mycoords(0,0, MyWin).y, red_color, orientation2[trial], mylambda2[trial], duty_cycle2, apertRad_pix, speed2)
        grating22 = Grating(MyWin, mycoords(0,0, MyWin).x - stereo2, mycoords(0,0, MyWin).y, cyan_color, orientation2[trial], mylambda2[trial], duty_cycle2, apertRad_pix, speed2)
        
        ######################################################  
        ## Wait for go Loop
        ######################################################
        while not wait_for_go_function(MyWin,lastevent) and not MyWin.has_exit:
            glClearColor(fg_color[0],fg_color[1],fg_color[2],1)             # set background color
            MyWin.clear()                                                   # clear window
            
            if trial_counter == 0:                                          # if first trial,
                lbl_instr.draw()                                            # show instructions
            
            else:                                                           # for the rest show fixation point
                lbl_instr2.draw()                                           # show instructions
                if fixYN:
                    drawCircle(xcenter, ycenter, numTheta, FPsize * 4, surrp_color)
                    drawCircle(xcenter, ycenter, numTheta, FPsize, fixp_color)
                
            MyWin.flip()                                                    # flip window


        ######################################################  
        ## Start stimulus loop
        ######################################################

        # Initialize forced variables
        if forced:
            i_R = 0
            i_L = 0
            Ron = 0
            Lon = 0
            timeTransR = transTimeL[0]
            timeTransL = transTimeR[0]
            deltaXaux1 = 0
            deltaXaux2 = 0


        timeStart = time.time()                                             # get trial start time
        
        eventcount += 1
        events_struct.append(EventItem(name = 'TrialEvent', counter = eventcount, timestamp = timeStart, etype = trial, eid = 'START'))
        if testing_with_eyetracker: controller.myRecordEvent2(EventItem(name = 'TrialEvent', counter = eventcount, timestamp = time.time(), etype = '{0} START'.format(trial), eid = timeStart))
        
        MyWin.reset_events()

        while (time.time() - timeStart) < timeCurrentTrial and not MyWin.has_exit:
            
            timeNow = time.time()                                           # get current time

            startMs = clock.tick()                                          # manual frame rate control: time point when frame starts. Also needed to show fps

            glClearColor(fg_color[0],fg_color[1],fg_color[2],1)             # set background color
            MyWin.clear()                                                   # clear window
            MyWin.dispatch_events()                                         # dispatch window events (very important call)

            ######################################################  
            ## Update position of objects
            ######################################################

            if forced:
                stereo1, stereo2, i_R, i_L, Ron, Lon, timeTransR, timeTransL, deltaXaux1, deltaXaux2 = compute_forced_values(
                    i_R, i_L, Ron, Lon, timeTransR, timeTransL, deltaXaux1, deltaXaux2, timeRamp, timeStart, timeNow, transTimeL, transTimeR)
            else:
                stereo1 = stereo1
                stereo2 = stereo2

            grating11.update_position(timeStart, stereo1)
            grating12.update_position(timeStart, stereo2)
            grating21.update_position(timeStart, stereo2)
            grating22.update_position(timeStart, stereo1)
            
        
            ######################################################  
            ## Draw objects
            ######################################################
            glEnable(GL_BLEND)
            
            drawAperture(xcenter, ycenter, apertRad_pix, aperture_color, numTheta)

            grating11.draw()
            grating12.draw()
            grating21.draw()
            grating22.draw()
            
            glDisable(GL_BLEND)

            if fixYN:
                drawCircle(xcenter, ycenter, numTheta, FPsize * 4, surrp_color)
                drawCircle(xcenter, ycenter, numTheta, FPsize, fixp_color)

            fps.draw()

            ######################################################  
            ## Flip the window
            ######################################################
            MyWin.flip()                                                        # flip window

            endMs = clock.tick() # manual frame rate control: time point when frame ends.
            # delaytime = frameMs - (endMs-startMs) # manual frame rate control: time time frame must be frozen.

        timeNow = time.time()
        


        ######################################################  
        ## Events
        ######################################################
        for e in MyWin.events:                                                  # get events from window
            eventcount += 1                                                     # increase counter for each event
            e.counter = eventcount                                              # copy counter
            events_struct.append(e)                                             # append to events_struct
            
            if testing_with_eyetracker: controller.myRecordEvent2(event = e)    # write event to eyetracker data file
        
        eventcount += 1
        events_struct.append(EventItem(name = 'TrialEvent', counter = eventcount, timestamp = timeNow, etype = trial, eid = 'END'))
        if testing_with_eyetracker: controller.myRecordEvent2(EventItem(name = 'TrialEvent', counter = eventcount, timestamp = timeNow, etype = '{0} END'.format(trial), eid = time.time()))


        if MyWin.has_exit:                                                      # This breaks the For stimulus loop. 
            break                                                               # Data is not lost, it has already been saved in the arrays.

    ###############################################################  
    ## Stop eyetracker processes, save data and close pyglet window
    ###############################################################
    if testing_with_eyetracker:
        controller.stopTracking()                                               # stop eye tracking and write output file
        controller.destroy()                                                    # destroy controller

    # save_raw_data(filename_rawdata, data_struct)                            # save raw data
    # save_data_formatted(filename_fordata,data_struct,right_keys,left_keys)  # save formatted data

    write_data_file(filename_data, events_struct)                               # write data file, it has raw and formatted data

    MyWin.close()                                                               # close pyglet window



    ######################################################  
    ######################################################

if __name__ == '__main__':
    print 'running 150121_Plaid_v19'

    if len(sys.argv) > 1:                           # optional: add a subject name
        subjectname = sys.argv[1]                   # run as python Plaid_v19 subjectname
    else:
        subjectname = 'defaultsubjectname'

    fps = pyglet.clock.ClockDisplay(color=(1,1,1,1)) # show frames per second
    main(subjectname = subjectname)
    
