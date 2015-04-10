import os, sys

lib_path = os.path.abspath(os.path.join('..','_Libraries'))
sys.path.append(lib_path)

from rlabs_libtobii import EyetrackerBrowser, MyTobiiController             # this is OUR library for the tobii eyetracker
from rlabs_libutils import *

from pyglet.window import Window
from pyglet.gl import *                                                     # to change the color of the background
from pyglet import clock

import time                                                                 # for the while loop
from random import shuffle                                                  # for calibration points
import itertools                                                            # to generate n target points

def main(
    ExpName = 'calibration_simulation', 
    subjectname = '', 
    testing_with_eyetracker = 0,
    npoints = 25,
    random_calibration_points = 1,
    time_point = 2
    ):

    # compute target point coordinates: 5, 9, 13 or 25 points
    array = [0.1, 0.5, 0.9] if npoints in (9,5) else [0.1, 0.3, 0.5, 0.7, 0.9]
    points = perm(array,2)
    if npoints in (5,13): points = points[::2]
    if random_calibration_points: shuffle(points)
    


    # create pyget window
    screens     = pyglet.window.get_platform().get_default_display().get_screens()
    MyWin       = MyWindow(fullscreen = True, screen = screens[0], visible = 0)
    xcenter     = MyWin.width/2
    ycenter     = MyWin.height/2
    framerate   = 60.0
    clock.set_fps_limit(framerate)                                          # set limit for frames per second
    fg_color    = (0.88, 0.88, 0.88)
    
    #-----------------------------------------------------  
    # Initialize variables for data file
    #-----------------------------------------------------
    
    # Name of the data files
    eyetrackeroutput   = os.path.join('data',(ExpName + "-" + time.strftime("%y.%m.%d_%H.%M", time.localtime()) + "_" + subjectname + "_" + "eyet" + ".txt"))
    filename_data      = os.path.join('data',(ExpName + "-" + time.strftime("%y.%m.%d_%H.%M", time.localtime()) + "_" + subjectname + "_" + "alldata" + ".txt"))
  
    lastevent = LastEvent()                                                 # LastEvent() is defined in rlabs_libutils
    events_struct = []
    eventcount = 0

    # Initialize text to be shown at startup
    textInstruc = "Click mouse-wheel to start calibration simulation"
    lbl_instr = pyglet.text.Label(
        text=textInstruc, font_name='Times New Roman', font_size=36, color=(0, 0, 0, 255), 
        x = MyWin.width/2, y = MyWin.height/2, anchor_x='center', anchor_y='center')


    # events_handler ---------------------------------------------------------------------------------------------------
    events_handler = {
        'on_mouse_press'    : lambda e: events_struct.append(e),
        'on_mouse_release'  : lambda e: events_struct.append(e),}

    events_handler_with_ET = {                      # if using eyetracker, use this
        'on_mouse_press'    : lambda e: (events_struct.append(e), controller.myRecordEvent2(event = e)),
        'on_mouse_release'  : lambda e: (events_struct.append(e), controller.myRecordEvent2(event = e)),}
    
    # Initialize eyetracker communication ----------------------------------------------------------------------
    if testing_with_eyetracker:
        # Create an EyetrackerBrowser and display it
        eb = EyetrackerBrowser()
        eb.main()

        # Initialize controller (MyTobiiController)
        controller = MyTobiiController(datafilename=eyetrackeroutput)       # create controller
        controller.waitForFindEyeTracker()                                  # wait to find eyetracker
        controller.activate(controller.eyetrackers.keys()[0])               # activate eyetracker
        controller.startTracking()                                          # start the eye tracking recording
        time.sleep(0.2)                                                     # wait for the eytracker to warm up

        MyWin.events_handler = events_handler_with_ET                       # set window events_handler with eye tracker

    else:
        MyWin.events_handler = events_handler                               # set window events_handler
    


    # startup screen. wait for go
    MyWin.set_visible(True)                                                 # set window to visible
    MyWin.set_mouse_visible(False)                                          # set mouse to not visible
    while not wait_for_go_function(MyWin,lastevent) and not MyWin.has_exit:
        glClearColor(fg_color[0],fg_color[1],fg_color[2],1)                 # set background color
        MyWin.clear()                                                       # clear window
        
        lbl_instr.draw()                                                    # show instructions      
           
        MyWin.flip()                                                        # flip window


    # CALIBRATION LOOP ----------------------------------------------------------------------------------------------------------------------------

    for point in points:                                                    # for each point
        timeStart = time.time()

        p_scaled = []
        p_scaled.append(point[0] * MyWin.width)                             # range horizontal coordinate to pyglet window
        p_scaled.append(MyWin.height - point[1] * MyWin.height)             # range vertical coordinate to pyglet window

        eventcount += 1
        events_struct.append(EventItem(name = 'TrialEvent', counter = eventcount, timestamp = timeStart, etype = point, eid = 'START'))
        if testing_with_eyetracker: controller.myRecordEvent2(EventItem(name = 'TrialEvent', counter = eventcount, timestamp = time.time(), etype = '{0} START'.format(point), eid = timeStart))
                   
        while (time.time() - timeStart) < time_point and not MyWin.has_exit:# show point

            glClearColor(fg_color[0],fg_color[1],fg_color[2],1)             # set background color
            MyWin.clear()                                                   # clear window
            MyWin.dispatch_events()                                         # dispatch window events (very important call)

            # check input
            lastevent = my_dispatch_events(MyWin, lastevent)                # my_dispatch_events is defined in rlabs_libutils
            if lastevent.type != []:                                        # check if last event is SPACE BAR or ...
                if lastevent.id == 32 and lastevent.type == "Key_UP":       # if it is space
                    lastevent.reset_values()                                # reset values of event
                    break

            # Draw target point
            drawCircle(p_scaled[0], p_scaled[1], radius = 10, color = (0,0,0))
            drawCircle(p_scaled[0], p_scaled[1], radius = 2, color = (1,1,1))

            MyWin.flip()                                                    # flip window

            pass

        timeNow = time.time()
        
        # events
        # for e in MyWin.events:                                                  # get events from window
        #     eventcount += 1                                                     # increase counter for each event
        #     e.counter = eventcount                                              # copy counter
        #     events_struct.append(e)                                             # append to events_struct
            
        #     if testing_with_eyetracker: controller.myRecordEvent2(event = e)    # write event to eyetracker data file
        
        eventcount += 1
        events_struct.append(EventItem(name = 'TrialEvent', counter = eventcount, timestamp = timeNow, etype = point, eid = 'END'))
        if testing_with_eyetracker: controller.myRecordEvent2(EventItem(name = 'TrialEvent', counter = eventcount, timestamp = timeNow, etype = '{0} END'.format(point), eid = time.time()))


        if MyWin.has_exit:                                                      # This breaks the For stimulus loop. 
            break                                                               # Data is not lost, it has already been saved in the arrays.



    #-------------------------------------------------------------
    # Stop eyetracker processes, save data and close pyglet window
    #-------------------------------------------------------------
    if testing_with_eyetracker:
        controller.stopTracking()                                               # stop eye tracking and write output file
        controller.destroy()                                                    # destroy controller

    # write_data_file(filename_data, events_struct)                               # write data file, it has raw and formatted data

    MyWin.close()                                                               # close pyglet window



    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':
    print 'running calibration simulation stimulus'

    if len(sys.argv) > 1:                           # optional: add a subject name
        subjectname = sys.argv[1]                   # run as python Plaid_v19 subjectname
    else:
        subjectname = 'defaultsubjectname'

    fps = pyglet.clock.ClockDisplay(color=(1,1,1,1)) # show frames per second
    main(subjectname = subjectname)
    
