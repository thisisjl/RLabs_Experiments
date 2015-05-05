"""
Creates a Plaid stimulus.

Execution: 
    $ python Plaid.py [optional name] 
    The optional name will be in the ouput data files, 
    if no specified "defaultsubjectname" will be used.

Input: 
    config_file.txt, trials_file.txt 
    (written in INI format, read using Python's ConfigParser module 
    (https://docs.python.org/2/library/configparser.html))

Output: 
    text file for button presses data and, if used, eyetracker data.

    Format of the button press (event) data: 7 + n columns, where n is the number of trials.
    column 1: time stamp. Time when the event was recorded
    column 2: event name. "InputEvent" for button presses, "TrialEvent" for start and end of trial.
    column 3: event type. If InputEvent, "Mouse_DW" for mouse button press, "Mouse_UP" for mouse buttton release. 
        If TrialEvent, number of trial.
    column 4: event id. If InputEvent, number of the button pressed. If TrialEvent, START or END.
    column 5: event code. Code used in analysis: 1 means LEFT button press, 
        -1 LEFT button press. 4/-4 for RIGHT button. 8 is trial start, -8 is trial end.
    column 6: event counter
    column 7: parameters name. Name of parameters used
    column 8 to 7+n: value of the parameter for each trial
    
    The eyetracker data contains 38 columns, 
    the first one is the eyetracker time stamp (computed by its own clock), 
    the rest of the colums are the different eye data that tobii offers in addition to the button press data.
"""

import os, sys

lib_path = os.path.abspath(os.path.join('..','_Libraries'))
sys.path.append(lib_path)

from rlabs_libtobii import EyetrackerBrowser, MyTobiiController             # this is OUR library for the tobii eyetracker
from rlabs_libutils import *

from pyglet.window import Window, mouse
from pyglet.gl import *                                                     # to change the color of the background
from pyglet import clock

import time                                                                 # for the while loop
from numpy.random import permutation as np_permutation                      # for random trials
from collections import OrderedDict
import ConfigParser                                                         # read parameter files

def main(
    ExpName = 'Plaid', 
    subjectname = '', 
    config_file = 'config_file.txt', 
    trials_file = 'trials_file.txt', 
    ):
    # Load parameters ------------------------------------------------------------------------
    if getattr(sys, 'frozen', False):                                       # path is different
        application_path = os.path.dirname(sys.executable)                  # if its an executable
    elif __file__:                                                          # or a Python script,
        application_path = os.path.dirname(__file__)                        # look for it

    # config_name = "config_file"                                             # Name of the config file
    # trials_name = "trials_file"                                             # Name of the trials file
    
    # config_name_full = os.path.join(application_path, config_name)  # Full path name of the config file
    # trials_name_full = os.path.join(application_path, trials_name)  # Full path name of the trials file

    cp = ConfigParser.SafeConfigParser()                                                                            # create a configParser instance
    cp.readfp(FakeSecHead(open(os.path.join(application_path,config_file))))                                                                       # read config_file and add fake header (INI file)
    cp = OrderedDict([(k,float(v) if len(v) < 7 else (map(float,v.split(',')))) for k,v in cp.items('asection')])   # read parameters of config_file in OrderedDict

    tp = ConfigParser.SafeConfigParser()                                                                            # create a configParser instance
    tp.readfp(FakeSecHead(open(os.path.join(application_path,trials_file))))                                                                       # read trials_file and add fake header (INI file)
    tp = OrderedDict([(k,float(v) if len(v) < 5 else map(float,v.split(','))) for k,v in tp.items('asection')])     # read parameters of config_file in OrderedDict

    parameters = merge_dicts_ordered(cp, tp)                                                                        # join parameters (to write them later)

    # randomize trials ?
    numtrials = int(tp['numtrials'])                                                            # get number of trials
    trials_array = np_permutation(numtrials) if cp['randomize_trials'] else range(numtrials)    # randomize trials or not

    # read forced transitions file
    if cp['forced']:
        transitions_file = filechooser()
        transitions_file_full = os.path.join(application_path, transitions_file)
        fs = Forced_struct(transfilename = transitions_file_full, timeRamp = cp['speed']) 

    # Initialize pyglet window ------------------------------------------------------------------------        
    screens = pyglet.window.get_platform().get_default_display().get_screens()
    if cp['aperture_switch']:
        allowstencil = pyglet.gl.Config(stencil_size = 8, double_buffer=True)
        MyWin = MyWindow(config=allowstencil, fullscreen = True, screen = screens[0], visible = 0)
    else:
        MyWin = MyWindow(fullscreen = True, screen = screens[0], visible = 0)
    
    xcenter = MyWin.width/2
    ycenter = MyWin.height/2

    clock.set_fps_limit(cp['framerate'])                                    # set limit for frames per second
    frameMs = 1000.0/cp['framerate']                                        # manual frame rate control: frameMs is the time in ms a frame will be displayed
  

    # Initialize variables for data file ----------------------------------------------------------------------
    if not os.path.isdir('data'):                                           # if there is not a folder called 'data',
        os.makedirs('data')                                                 # create it
    # Name of the data files
    eyetrackeroutput   = os.path.join(application_path, os.path.join('data',(ExpName + "-" + time.strftime("%y.%m.%d_%H.%M", time.localtime()) + "_" + subjectname + "_" + "eyetracker_data" + ".txt")))
    filename_data      = os.path.join(application_path, os.path.join('data',(ExpName + "-" + time.strftime("%y.%m.%d_%H.%M", time.localtime()) + "_" + subjectname + "_" + "button_press_data" + ".txt")))
    filename_transtns  = os.path.join(application_path, os.path.join('data',(ExpName + "-" + time.strftime("%y.%m.%d_%H.%M", time.localtime()) + "_" + subjectname + "_" + "transitions_file" + ".txt")))
   
    # 3.4 - Initialize text to be shown at startup (not whown right now)
    textInstruc = "Continually report the motion of the grating in front.\nPress the left mouse button for left-ward motion.\nPress the right mouse button for right-ward motion\n\nClick mouse-wheel to start"
    lbl_instr = pyglet.text.Label(text=textInstruc, font_name='Times New Roman', font_size=36,
        color=(0, 0, 0, 255), x = MyWin.width/2+120, y = MyWin.height/2, anchor_x='center', anchor_y='center', width=MyWin.width/1, multiline=True)

    textInstruc2 = "Click mouse-wheel for next trial"
    lbl_instr2 = pyglet.text.Label(text=textInstruc2, font_name='Times New Roman', font_size=24,
        color=(0, 0, 0, 255), x = MyWin.width/2, y = MyWin.height/2.4, anchor_x='center', anchor_y='center')

    # handling events ---------------------------------------------------------------------------------------------------
    
    events_struct = []                                                      # list that contains event that the event handler sends.
    eventcount = 0                                                          # counter of the events

    events_handler = {                                                      # events handler (it needs to be set to window)
        'on_mouse_press'    : lambda e: events_struct.append(e),            # append on_mouse_press event to events_struct
        'on_mouse_release'  : lambda e: events_struct.append(e),}           # append on_mouse_release event to events_struct

    events_handler_with_ET = {                                                                              # if using eyetracker, this will add
        'on_mouse_press'    : lambda e: (events_struct.append(e), controller.myRecordEvent2(event = e)),    # to events_struct and also it will 
        'on_mouse_release'  : lambda e: (events_struct.append(e), controller.myRecordEvent2(event = e)),}   # call MyRecordEvent2 with the event


    # Initialize eyetracker communication ----------------------------------------------------------------------
    if cp['eyetracker']:
        eb = EyetrackerBrowser()                                            # Create an EyetrackerBrowser
        eb.main()                                                           # and display it

        # Initialize controller (MyTobiiController)
        controller = MyTobiiController(                                     # create controller
            datafilename = eyetrackeroutput,                                # pass it the eyetracker data name
            parameters = parameters)                                        # pass it the parameters
        controller.waitForFindEyeTracker()                                  # wait to find eyetracker
        controller.activate(controller.eyetrackers.keys()[0])               # activate eyetracker

        # (start trials)
        controller.startTracking()                                          # start the eye tracking recording
        time.sleep(0.2)                                                     # wait for the eytracker to warm up

        MyWin.events_handler = events_handler_with_ET                       # set window events_handler with eye tracker

    else:
        MyWin.events_handler = events_handler                               # set window events_handler


    # Start trials ---------------------------------------------------------------------------------------------

    MyWin.set_visible(True)                                                 # set window to visible
    MyWin.set_mouse_visible(False)                                          # set mouse to not visible
    timeStart_general = time.time()                                         # get general start time
    
    for trial_counter in range(numtrials):                                  # for each trial 

        # Prepare variables before stimulus loop ------------------------------------------------------------------
        trial = trials_array[trial_counter]

        apertRad_pix = MyWin.height / cp['aperturediv']
        
        grating11 = Grating(MyWin, mycoords(0,0, MyWin).x + cp['stereo1'], mycoords(0,0, MyWin).y, cp['red_color'],  tp['orientation1'][trial], tp['mylambda1'][trial], tp['duty_cycle1'][trial], apertRad_pix, tp['speed1'][trial])
        grating12 = Grating(MyWin, mycoords(0,0, MyWin).x - cp['stereo1'], mycoords(0,0, MyWin).y, cp['cyan_color'], tp['orientation1'][trial], tp['mylambda1'][trial], tp['duty_cycle1'][trial], apertRad_pix, tp['speed1'][trial])
        grating21 = Grating(MyWin, mycoords(0,0, MyWin).x + cp['stereo2'], mycoords(0,0, MyWin).y, cp['red_color'],  tp['orientation2'][trial], tp['mylambda2'][trial], tp['duty_cycle2'][trial], apertRad_pix, tp['speed2'][trial])
        grating22 = Grating(MyWin, mycoords(0,0, MyWin).x - cp['stereo2'], mycoords(0,0, MyWin).y, cp['cyan_color'], tp['orientation2'][trial], tp['mylambda2'][trial], tp['duty_cycle2'][trial], apertRad_pix, tp['speed2'][trial])
        
        # Wait for go Loop ---------------------------------------------------------------------------------------------
        wait = True                                                         # wait for go condition: wait
        while wait and not MyWin.has_exit:
            glClearColor(cp['fg_color'][0],cp['fg_color'][1],cp['fg_color'][2],1)             # set background color
            MyWin.clear()                                                   # clear window
            MyWin.dispatch_events()                                         # dispatch window events (very important call)
            
            if trial_counter == 0:                                          # if first trial,
                lbl_instr.draw()                                            # show instructions number 1
            else:                                                           # for the rest
                lbl_instr2.draw()                                           # show instructions number 2

                if cp['fixationpoint'] == 1: #'Circle with protection zone':
                    drawCircle(xcenter, ycenter, cp['fpsize'] * 4, cp['surrp_color'])
                    drawCircle(xcenter, ycenter, cp['fpsize'], cp['fixp_color'])
                if cp['fixationpoint'] == 2: #'Circle without protection zone':
                    drawCircle(xcenter, ycenter, cp['fpsize'], cp['fixp_color'])
                if cp['fixationpoint'] == 3: #'Cross':
                    draw_cross(xcenter, ycenter, length1 = 50, length2 = 50)

            last_event = MyWin.get_last_event()                                                 # get last event on MyWin
            if last_event and last_event.id == mouse.MIDDLE and last_event.type == 'Mouse_UP':  # if id and type match to the release of middle button,
                wait = False                                                                    # do not wait, exit wait for go loop

            MyWin.flip()                                                    # flip window

        # Start stimulus loop -------------------------------------------------------------------------------------------------------------

        if cp['forced']:
            fs.reset_forced_values(trial = trial)                           # Initialize forced variables


        timeStart = time.time()                                             # get trial start time
        
        eventcount += 1
        events_struct.append(EventItem(name = 'TrialEvent', counter = eventcount, timestamp = timeStart, etype = trial, eid = 'START'))
        if cp['eyetracker']: controller.myRecordEvent2(EventItem(name = 'TrialEvent', counter = eventcount, timestamp = time.time(), etype = trial, eid = 'START'))
        
        MyWin.reset_events()

        while (time.time() - timeStart) < tp['timetrial'] and not MyWin.has_exit:
            
            timeNow = time.time()                                           # get current time

            startMs = clock.tick()                                          # manual frame rate control: time point when frame starts. Also needed to show fps

            glClearColor(cp['fg_color'][0],cp['fg_color'][1],cp['fg_color'][2],1)             # set background color
            MyWin.clear()                                                   # clear window
            MyWin.dispatch_events()                                         # dispatch window events (very important call)

            
            # Update position of objects ---------------------------------------------------------------------------------------------------

            if cp['forced']:
                stereo1, stereo2 = fs.compute_forced_values(timeStart, timeNow)


            else:
                stereo1 = cp['stereo1']
                stereo2 = cp['stereo2']

            grating11.update_position(timeStart, stereo1)
            grating12.update_position(timeStart, stereo2)
            grating21.update_position(timeStart, stereo2)
            grating22.update_position(timeStart, stereo1)
            
        
            # Draw objects ---------------------------------------------------------------------------------------------------

            glEnable(GL_BLEND)
            
            drawAperture(xcenter, ycenter, apertRad_pix, cp['aperture_color'])

            grating11.draw()
            grating12.draw()
            grating21.draw()
            grating22.draw()
            
            glDisable(GL_BLEND)

            if cp['fixationpoint'] == 1: #'Circle with protection zone':
                drawCircle(xcenter, ycenter, cp['fpsize'] * 4, cp['surrp_color'])
                drawCircle(xcenter, ycenter, cp['fpsize'], cp['fixp_color'])
            if cp['fixationpoint'] == 2: #'Circle without protection zone':
                drawCircle(xcenter, ycenter, cp['fpsize'], cp['fixp_color'])
            if cp['fixationpoint'] == 3: #'Cross':
                draw_cross(xcenter, ycenter, length1 = 50, length2 = 50)

            fps.draw()


            # Flip the window
            MyWin.flip()                                                        # flip window

            endMs = clock.tick() # manual frame rate control: time point when frame ends.
            # delaytime = frameMs - (endMs-startMs) # manual frame rate control: time time frame must be frozen.

        timeNow = time.time()
        
        # # Events ---------------------------------------------------------------------------------------------------
        # for e in MyWin.events:                                                  # get events from window
        #     eventcount += 1                                                     # increase counter for each event
        #     e.counter = eventcount                                              # copy counter
        #     # events_struct.append(e)                                             # append to events_struct
            
        #     # if cp['eyetracker']: controller.myRecordEvent2(event = e)    # write event to eyetracker data file
        
        eventcount += 1
        events_struct.append(EventItem(name = 'TrialEvent', counter = eventcount, timestamp = timeNow, etype = trial, eid = 'END'))
        if cp['eyetracker']: controller.myRecordEvent2(EventItem(name = 'TrialEvent', counter = eventcount, timestamp = timeNow, etype = trial, eid ='END'))


        if MyWin.has_exit:                                                      # This breaks the For stimulus loop. 
            break                                                               # Data is not lost, it has already been saved in the arrays.


    # Stop eyetracker processes, save data and close pyglet window ------------------------------------------------------------------------
    if cp['eyetracker']:
        controller.stopTracking()                                               # stop eye tracking and write output file
        controller.destroy()                                                    # destroy controller

    write_data_file_with_parameters(filename_data, events_struct, parameters)   # write data file, it has raw and formatted data
    
    if cp['create_transitions']:
        create_transitions_file(infilename = filename_data, outfilename = filename_transtns)

    MyWin.close()                                                               # close pyglet window




    # -------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    print 'running Plaid'

    if len(sys.argv) > 1:                           # optional: to add a subject name
        subjectname = sys.argv[1]                   # run as python Plaid subjectname
    else:                                           # if no subject name specified
        subjectname = 'defaultsubjectname'          # this will be used

    fps = pyglet.clock.ClockDisplay(color=(1,1,1,1)) # show frames per second
    main(subjectname = subjectname)
    
