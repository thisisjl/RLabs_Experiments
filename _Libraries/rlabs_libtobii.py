#!/usr/bin/python
# in TobiiTracker.controller

# TobiiController
from tobii.eye_tracking_io.basic import EyetrackerException

import tobii.eye_tracking_io.mainloop
import tobii.eye_tracking_io.browsing
import tobii.eye_tracking_io.eyetracker
import tobii.eye_tracking_io.time.clock
import tobii.eye_tracking_io.time.sync

# in tobii SDK EyetrackerBrowser, for the calibration
import pygtk
pygtk.require('2.0')
import gtk

glib_idle_add = None
glib_timeout_add = None
try:
    import glib
    glib_idle_add = glib.idle_add
    glib_timeout_add = glib.timeout_add
except:
    glib_idle_add = gtk.idle_add
    glib_timeout_add = gtk.timeout_add

from tobii.eye_tracking_io.types import Point2D, Blob

import math

from random import shuffle                                      # for calibration points
from rlabs_libutils import *
from pyglet.window import Window, mouse, key
import pyglet

import sys
import os, stat                                                 # to create read-only file
import time
##########################################################################
## Copied (and slightly modified) from Tobii SDK's EyetrackerBrowser.py 
##########################################################################

class TrackStatus(gtk.DrawingArea):
    MAX_AGE = 30.0
    
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.eyetracker = None
        self.set_size_request(300, 300)
        self.connect("expose_event", self.on_expose)
        
        self.gazedata = None
        self.gaze_data_history = []
   
    def set_eyetracker(self, eyetracker):
        if self.eyetracker is not None:
            self.eyetracker.StopTracking()
            self.eyetracker.events.OnGazeDataReceived -= self.on_gazedata
        
        self.eyetracker = eyetracker
        self.gazedata = None
        if self.eyetracker is not None:
            self.eyetracker.events.OnGazeDataReceived += self.on_gazedata
            self.eyetracker.StartTracking()
    
    def on_gazedata(self, error, gaze):
        if hasattr(gaze, 'TrigSignal'):
            print "Trig signal:", gaze.TrigSignal
               
        gazedata_copy = { 'left': { 'validity':     gaze.LeftValidity,
                                    'camera_pos':   gaze.LeftEyePosition3DRelative,
                                    'screen_pos':   gaze.LeftGazePoint2D },
                          'right': { 'validity':    gaze.RightValidity,             
                                     'camera_pos':  gaze.RightEyePosition3DRelative,
                                     'screen_pos':  gaze.RightGazePoint2D          }} 
        try:
            glib_idle_add(self.handle_gazedata, error, gazedata_copy)
        except Exception, ex:
            print "  Exception occured: %s" %(ex)

    def handle_gazedata(self, error, gazedata):
        self.gazedata = gazedata
        self.gaze_data_history.append(self.gazedata)
        if len(self.gaze_data_history) > TrackStatus.MAX_AGE:
            self.gaze_data_history.pop(0)
        self.redraw()

    def redraw(self):
        if self.window:
            alloc = self.get_allocation()
            rect = gtk.gdk.Rectangle(0, 0, alloc.width, alloc.height)
            self.window.invalidate_rect(rect, True)
            self.window.process_updates(True)

    def draw_eye(self, ctx, validity, camera_pos, screen_pos, age):
        screen_pos_x = screen_pos.x - .5
        screen_pos_y = screen_pos.y - .5
        
        eye_radius = 0.075
        iris_radius = 0.03
        pupil_radius = 0.01

        opacity = 1 - age * 1.0 / TrackStatus.MAX_AGE
        if validity <= 1:
            ctx.set_source_rgba(1, 1, 1, opacity)
            ctx.arc(1 - camera_pos.x, camera_pos.y, eye_radius, 0, 2 * math.pi)
            ctx.fill()

            ctx.set_source_rgba(.5, .5, 1, opacity)
            ctx.arc(1 - camera_pos.x + ((eye_radius - iris_radius / 2) * screen_pos_x), camera_pos.y + ((eye_radius - iris_radius / 2) * screen_pos_y), iris_radius, 0, 2 * math.pi)
            ctx.fill()
            
            ctx.set_source_rgba(0, 0, 0, opacity)
            ctx.arc(1 - camera_pos.x + ((eye_radius - iris_radius / 2) * screen_pos_x), camera_pos.y + ((eye_radius - iris_radius / 2) * screen_pos_y), pupil_radius, 0, 2 * math.pi)
            ctx.fill()

    def draw(self, ctx):
        ctx.set_source_rgb(0., 0., 0.)
        ctx.rectangle(0, 0, 1, .9)
        ctx.fill()
        
        # paint left rectangle
        if self.gazedata is not None and self.gazedata['left']['validity'] == 0:
            ctx.set_source_rgb(0, 1, 0)
        else:
            ctx.set_source_rgb(1, 0, 0)
        ctx.rectangle(0, .9, .5, 1)
        ctx.fill()
        
        # paint right rectangle
        if self.gazedata is not None and self.gazedata['right']['validity'] == 0:
            ctx.set_source_rgb(0, 1, 0)
        else:
            ctx.set_source_rgb(1, 0, 0)
        ctx.rectangle(.5, .9, 1, 1)
        ctx.fill()
        
        if self.gazedata is None:
            return
        
        # paint eyes
        for eye in ('left', 'right'):
            (validity, age, camera_pos, screen_pos) = self.find_gaze(eye)
            self.draw_eye(ctx, validity, camera_pos, screen_pos, age)

    def find_gaze(self, eye):
        i = 0
        for gaze in reversed(self.gaze_data_history):
            if gaze[eye]['validity'] <= 1:
                return (gaze[eye]['validity'], i, gaze[eye]['camera_pos'], gaze[eye]['screen_pos'])
            i += 1
        return (gaze[eye]['validity'], 0, gaze[eye]['camera_pos'], gaze[eye]['screen_pos'])

    def on_expose(self, widget, event):
        context = widget.window.cairo_create()
        context.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        context.clip()
        
        rect = widget.get_allocation()
        context.scale(rect.width, rect.height)

        self.draw(context)
        return False


class CalibPlot(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)

        self.set_size_request(300, 300)
        self.connect("expose_event", self.on_expose)
        
        self.calib = None
    
    def set_eyetracker(self, eyetracker):
        if eyetracker is None:
            return
        
        try:
            self.calib = eyetracker.GetCalibration(lambda error, calib: glib_idle_add(self.on_calib_response, error, calib))
        except Exception, ex:
            print "  Exception occured: %s" %(ex)
            self.calib = None
        self.redraw()
    
    def on_calib_response(self, error, calib):
        if error:
            print "on_calib_response: Error"
            self.calib = None
            self.redraw()
            return False
        
        self.calib = calib
        self.redraw()
        return False
            
    def redraw(self):
        if self.window:
            alloc = self.get_allocation()
            rect = gtk.gdk.Rectangle(0, 0, alloc.width, alloc.height)
            self.window.invalidate_rect(rect, True)
            self.window.process_updates(True)
    
    def on_expose(self, widget, event):
        context = widget.window.cairo_create()
        context.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        context.clip()
        
        rect = widget.get_allocation()
        context.scale(rect.width, rect.height)

        self.draw(context)
    
    def draw(self, ctx):
        ctx.rectangle(0, 0, 1, 1)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()
        
        if self.calib is None:
            ctx.move_to(0, 0)
            ctx.line_to(1, 1)
            ctx.move_to(0, 1)
            ctx.line_to(1, 0)
            ctx.set_source_rgb(0, 0, 0)
            ctx.set_line_width(0.001)
            ctx.stroke()
            return
        
        points = {}
        for data in self.calib.plot_data:
            points[data.true_point] = { 'left': data.left, 'right': data.right }
        
        if len(points) == 0:
            ctx.move_to(0, 0)
            ctx.line_to(1, 1)
            ctx.move_to(0, 1)
            ctx.line_to(1, 0)
            ctx.set_source_rgb(0, 0, 0)
            ctx.set_line_width(0.001)
            ctx.stroke()
            return
        
        for p, d in points.iteritems():
            ctx.set_line_width(0.001)
            if d['left'].status == 1:
                ctx.set_source_rgb(1.0, 0., 0.)
                ctx.move_to(p.x, p.y)
                ctx.line_to(d['left'].map_point.x, d['left'].map_point.y)
                ctx.stroke()

            if d['right'].status == 1:            
                ctx.set_source_rgb(0., 1.0, 0.)
                ctx.move_to(p.x, p.y)
                ctx.line_to(d['right'].map_point.x, d['right'].map_point.y)
                ctx.stroke()
        
            ctx.set_line_width(0.005)
            ctx.set_source_rgba(0., 0., 0., 0.05)
            ctx.arc(p.x, p.y, 0.01, 0, 2 * math.pi)
            ctx.stroke ()


class Calibration:
    def __init__(self, verbose = 0):                                # added verbose
        # print 'calibration - init'
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        # print self.window.get_screen()                              # added -------------------------------------------------------------------------------
        self.canvas = gtk.DrawingArea()
        self.window.add(self.canvas)
        self.canvas.connect("expose_event", self.on_expose)
        self.window.connect("key_press_event", self.on_key_press)

        self.points = [(0.1,0.1), (0.9,0.1) , (0.5,0.5), (0.1,0.9), (0.9,0.9)]
        shuffle(self.points)                                             # jl modified: random calibration points

        self.point_index = -1
        self.on_calib_done = None

        self.verbose = verbose

    def run(self, tracker, on_calib_done):
        if self.verbose: print 'calibration - run'
        self.window.fullscreen()
        self.window.show_all()
        self.on_calib_done = on_calib_done
        self.tracker = tracker
        self.point_index = -1
        self.tracker.StartCalibration(lambda error, r: glib_idle_add(self.on_calib_start, error, r))
        
    def on_calib_start(self, error, r):
        if self.verbose: print 'calibration - on_calib_start'
        if error:
            self.on_calib_done(False, "Could not start calibration because of error. (0x%0x)" % error)
            return False
        
        self.wait_for_add()
        return False
        
    
    def on_expose(self, widget, event):
        if self.verbose: print 'calibration - on_expose'
        context = widget.window.cairo_create()
        # context.set_source_rgb(0.88*255,0.88*255,0.88*255)                                 # modified line: this was not here at all
        context.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        context.clip()
        
        # self.draw(context)
        self.draw(context,event)
        return False
    
    # def draw(self,ctx):
    def draw(self,ctx,event):
        if self.verbose: print 'calibration - draw'
        
        # ctx.set_source_rgb(0.7*255,0.70*255,0.70*255)                                 # modified line: this was not here at all
        ctx.set_source_rgb(0.88,0.88,0.88)                                 # modified line: this was not here at all
        ctx.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        ctx.fill()

        if self.point_index >= 0:                                           # modified line: 0 was -1
            x,y = self.points[self.point_index]
            bounds = self.canvas.get_allocation()
            # Draw calibration dot
            ctx.set_source_rgb(255,0,0)
            radius = 0.012*bounds.width
            ctx.arc(bounds.width*x, bounds.height*y, radius,0, 2 * math.pi)
            ctx.fill()
            
            # Draw center dot
            ctx.set_source_rgb(0,0,0);
            radius = 2;
            ctx.arc(bounds.width*x, bounds.height*y, radius,0, 2 * math.pi)
            ctx.fill()
            
            
    def wait_for_add(self):
        if self.verbose: print 'calibration - wait_for_add'
        self.point_index += 1
        self.redraw()

        # we should add here wait for key press, 
        # wait for space

        # glib_timeout_add(500, self.add_point)
    
    def add_point(self):
        if self.verbose: print 'calibration - add_point'
        p = Point2D()
        p.x, p.y = self.points[self.point_index]
        self.tracker.AddCalibrationPoint(p, lambda error, r: glib_idle_add(self.on_add_completed, error, r))
        return False

    def on_add_completed(self, error, r):
        if self.verbose: print 'calibration - on_add_completed'
        if error:
            self.on_calib_done(False, "Add Calibration Point failed because of error. (0x%0x)" % error)
            return False
        
        if self.point_index == len(self.points) - 1:
            #This was the last calibration point
            self.tracker.ComputeCalibration(lambda error, r: glib_idle_add(self.on_calib_compute, error, r))
        else:
            self.wait_for_add()
        
        return False

    def on_calib_compute(self, error, r):
        if self.verbose: print 'calibration - on_calib_compute'
        if error == 0x20000502:
            print "CalibCompute failed because not enough data was collected"
            self.on_calib_done(False, "Not enough data was collected during calibration procedure.")
        elif error != 0:
            print "CalibCompute failed because of a server error"
            self.on_calib_done(False, "Could not compute calibration because of a server error.\n\n<b>Details:</b>\n<i>%s</i>" % (error))
        else:
            self.on_calib_done(True, "")
        self.tracker.StopCalibration(None)
        self.window.destroy()
        return False
    
    def redraw(self):
        if self.verbose: print 'calibration - redraw'
        if self.canvas.window:
            alloc = self.canvas.get_allocation()
            rect = gtk.gdk.Rectangle(0, 0, alloc.width, alloc.height)
            self.canvas.window.invalidate_rect(rect, True)

    def on_key_press(self, widget, event):
        if self.verbose: print 'calibration - on_key_press'
        keyname = gtk.gdk.keyval_name(event.keyval)         # this is the name of the pressed key, eg: 'Escape', 'f'

        if keyname == 'Escape':                             # this should make the calibration stop
            print 'Calibration exited by user'
            self.tracker.StopCalibration(None)
            self.window.destroy()
            # return False
            # w.emit("delete-event", gtk.gdk.Event(gtk.gdk.DELETE))

        if keyname == 'space':
            self.add_point()                                # this should change

class MyCalibration:

    def runCalibration(self, eyetracker, npoints = 5, random_calibration_points = 1,):

        self._lastCalibrationOK=False
        self._lastCalibrationReturnCode=0
        self._lastCalibration=None
        self.point_index = 0

        self.eyetracker = eyetracker
        calibration_sequence_completed=False        
        
        MyWin = Window(fullscreen=True, visible = 0)

        instuction_text="Press mouse MIDDLE button to Start Calibration; ESCAPE to Exit."           # instructions to show before calibration
        mylabel = pyglet.text.Label(instuction_text, font_name = 'Times New Roman', font_size = 36, # create label that contain instructions
            color=(0, 0, 0, 255), x = MyWin.width/2, y = MyWin.height/2, multiline = True,          
            width=600, anchor_x = "center", anchor_y = "center")                                    
       
        fg_color = (0.88,0.88,0.88)                                                                 # background color

        # compute target point coordinates: 5, 9, 13 or 25 points ----------------------------------
        tparray = [0.1, 0.5, 0.9] if npoints in (9,5) else [0.1, 0.3, 0.5, 0.7, 0.9]                # using a different array if 5-9 or 13-25 points
        points = perm(tparray,2)                                                                    # combine tparray to compute position of target points
        if npoints in (5,13): points = points[::2]                                                  # if 5 or 13 points, only use even elements
        if random_calibration_points: shuffle(points)                                               # if random points, shuffle
        p = Point2D()                                                                               # Tobii expects positin in Point2D() format
        
        MyWin.set_visible(True)                                                                     # set window to visible
        MyWin.set_mouse_visible(False)                                                              # set mouse to not visible

        # Wait for go Loop ---------------------------------------------------------------------------------------------
        wait = True                                                                                 # wait for go condition: wait
        while wait and not MyWin.has_exit:
            MyWin.clear()                                                                           # clear window
            MyWin.dispatch_events()                                                                 # dispatch window events (very important call)

            last_event = MyWin.get_last_event()                                                     # get last event on MyWin
            if last_event and last_event.id == mouse.MIDDLE and last_event.type == 'Mouse_UP':      # if id and type match to the release of middle button,
                continue_calibration = True
                wait = False                                                                        # do not wait, exit wait for go loop
            if last_event and last_event.id == key.ESCAPE and last_event.type == 'Key_UP':          # if id and type match to the release of escape key,
                continue_calibration = False                                                        # do not continue to calibration
                wait = False                                                                        # do not wait, exit wait for go loop

            mylabel.draw()                                                                          # show message
            MyWin.flip()                                                                            # flip window

        if not continue_calibration:                                                                # if escape was pressed,
            print 'continue calibration is false'
            return False                                                                            # exit calibration

        # CALIBRATION LOOP -------------------------------------------------------------------------
        self.eyetracker.StartCalibration(self.on_start_calibration)                                 # start calibration

        for point in points:                                                                        # for each point

            p_scaled = []
            p_scaled.append(point[0] * MyWin.width)                                                 # range horizontal coordinate to pyglet window
            p_scaled.append(MyWin.height - point[1] * MyWin.height)                                 # range vertical coordinate to pyglet window
                       
            while not MyWin.has_exit:                                                               # show point

                glClearColor(fg_color[0],fg_color[1],fg_color[2],1)                                 # set background color
                MyWin.clear()                                                                       # clear window
                MyWin.dispatch_events()                                                             # dispatch window events (very important call)

                ## Check events (mouse input)
                last_event = win.get_last_event()                                                   # get last event on MyWin
                if last_event and last_event.id == mouse.MIDDLE and last_event.type == 'Mouse_UP':  # if id and type match to the release of middle button,
                    win.reset_last_event()                                                          # reset last_event
                    break                                                                           # break while loop (move point to new location)

                # Draw point
                drawCircle(p_scaled[0], p_scaled[1], radius = 10, color = (0,0,0))
                drawCircle(p_scaled[0], p_scaled[1], radius = 3, color = (1,1,1))

                # Flip the window
                MyWin.flip()                                                                        # flip window


            # Add point to eyetracker (point not scaled) ------------------------------------------
            p.x, p.y = point
            self.eyetracker.AddCalibrationPoint(p,self.on_add_calibration_point)                    # add calibration point to eyetracker
            time.sleep(0.5)            
            
            self.point_index += 1                                                                   # increase point iterator
            if self.point_index == len(points):                                                     # if last points
                calibration_sequence_completed=True                                                 # end calibration
            
            if MyWin.has_exit:                                                                      # This breaks the For stimulus loop. 
                break

        # calibration completed -------------------------------------------------------------------
        if calibration_sequence_completed:
            self.eyetracker.ComputeCalibration(self.on_compute_calibration)                         # compute calibration

        self.eyetracker.StopCalibration(None)                                                       # stop calibration

        MyWin.close()                                                                               # close window

        if self._lastCalibrationOK is True:
            # reset_calibration = self.show_calibration(MyWin)
            # self._tobii.GetCalibration(self.on_calibration_result)
            # calibration_result = self.eyetracker.GetCalibration(self.on_calibration_result)
            return True
            pass

        if self._lastCalibrationOK is False:
            print '_lastCalibrationOK is False'
            return False

        if reset_calibration:
            pass

        pass

    def on_start_calibration(self,*args,**kwargs):
        #ioHub.print2err('on_start_calibration: ',args,kwargs)
        pass
    
    def on_add_calibration_point(self,*args,**kwargs):
        pass

    def on_compute_calibration(self,*args,**kwargs):
        self._lastCalibrationReturnCode=args[0]
        if self._lastCalibrationReturnCode!=0:
            print2err("ERROR: Tobii Calibration Calculation Failed. Error code: {0}".format(self._lastCalibrationReturnCode))
            self._lastCalibrationOK=False
            # self._msg_queue.put("CALIBRATION_COMPUTATION_FAILED")
        
        else:
            # self._msg_queue.put("CALIBRATION_COMPUTATION_COMPLETE")
            self._lastCalibrationOK=True
            pass

    def show_calibration(self, MyWin):

        left_color = (1.0, 0., 0.)
        rigth_color = (0., 1.0, 0.)

        reset_calibration = 0

        try:
            self.clibration_result = self.eyetracker.GetCalibration()
        except Exception, ex:
            print "  Exception occured: %s" %(ex)
            self.clibration_result = None


        if self.clibration_result is None:
            print 'Show Calibration Error: calibration_result is None'
            return
        
        points = {}
        for data in self.clibration_result.plot_data:
            points[data.true_point] = { 'left': data.left, 'right': data.right }
        
        if len(points) == 0:
            print 'Show Calibration Error: len(points) is 0'
            return
        
        ######################################################  
        ## Draw calibration
        ######################################################
        show_clibration_results = True
        while show_clibration_results:# and not MyWin.has_exit:               # Show welcome text for calibration
            
            ## CLEAR WINDOW
            MyWin.clear()                                                   # clear window
            MyWin.dispatch_events()                                         # dispatch window events (very important call)            
            
            ## CHECK INPUT
            lastevent = my_dispatch_events(MyWin, lastevent)                # my_dispatch_events is defined in rlabs_libutils
            if lastevent.type != []:                                        # check if last event is SPACE or ...
                if lastevent.id == 32 and lastevent.type == "Key_UP":       # if it is space, break while loop
                    lastevent.reset_values()                                # reset values of event
                    show_clibration_results = False
                    reset_calibration = 0
                    print 'Show Calibration: Continue'

                if lastevent.id == 27 and lastevent.type == "Key_UP":       # if it is escape, return false
                    lastevent.reset_values()                                # reset values of event
                    show_clibration_results = False
                    reset_calibration = 1
                    print 'Show Calibration: Reset calibration'
                
            ## DRAW

            for p, d in points.iteritems():                                 # p is the target point [x,y]
                                                                            # d is...
                if d['left'].status == 1:
                    dest = (d['left'].map_point.x, d['left'].map_point.y)
                    drawline(p, dest, color = left_color)

                if d['right'].status == 1:
                    dest = (d['right'].map_point.x, d['right'].map_point.y)
                    drawline(p, dest, color = right_color)

            MyWin.flip()                                                    # flip window


        return reset_calibration

        # This function should ask to continue or not.

        pass
   
def show_message_box(parent, message, title="", buttons=gtk.BUTTONS_OK):
    def close_dialog(dlg, rid):
        dlg.destroy()

    msg = gtk.MessageDialog(parent=parent, buttons=buttons)
    msg.set_markup(message)
    msg.set_modal(False)
    msg.connect("response", close_dialog)
    msg.show()


class EyetrackerBrowser:

    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.window.set_border_width(5)
        self.window.set_size_request(960, 480)
        # self.window.fullscreen()

        self.eyetracker = None
        self.eyetrackers = {}        
        self.liststore = gtk.ListStore(str, str, str)

        self.treeview = gtk.TreeView(self.liststore)
        self.treeview.connect("row-activated", self.row_activated)

        self.pid_column = gtk.TreeViewColumn("PID")
        self.pid_cell = gtk.CellRendererText()
        self.treeview.append_column(self.pid_column)
        self.pid_column.pack_start(self.pid_cell, True)
        self.pid_column.set_attributes(self.pid_cell, text=0)

        self.model_column = gtk.TreeViewColumn("Model")
        self.model_cell = gtk.CellRendererText()
        self.treeview.append_column(self.model_column)
        self.model_column.pack_start(self.model_cell, True)
        self.model_column.set_attributes(self.model_cell, text=1)

        self.status_column = gtk.TreeViewColumn("Status")
        self.status_cell = gtk.CellRendererText()
        self.treeview.append_column(self.status_column)
        self.status_column.pack_start(self.status_cell, True)
        self.status_column.set_attributes(self.status_cell, text=2)

        self.trackstatus = TrackStatus()
        self.calibplot = CalibPlot()

        self.table = gtk.Table(3, 3)
        self.table.set_col_spacings(4)
        self.table.set_row_spacings(4)

        self.treeview_label = gtk.Label()
        self.treeview_label.set_alignment(0.0, 0.5)
        self.treeview_label.set_markup("<b>Discovered Eyetrackers:</b>")
        self.table.attach(self.treeview_label, 0, 1, 0, 1, xoptions=gtk.FILL, yoptions=gtk.FILL)
        self.table.attach(self.treeview, 0, 1, 1, 2)
        
        self.calibplot_label = gtk.Label()
        self.calibplot_label.set_markup("<b>Calibration Plot:</b>")
        self.calibplot_label.set_alignment(0.0, 0.5)
        self.table.attach(self.calibplot_label, 1, 2, 0, 1, xoptions=gtk.FILL, yoptions=gtk.FILL)
        self.table.attach(self.calibplot, 1, 2, 1, 2)
        
        self.trackstatus_label = gtk.Label()
        self.trackstatus_label.set_markup("<b>Trackstatus:</b>")
        self.trackstatus_label.set_alignment(0.0, 0.5)
        self.table.attach(self.trackstatus_label, 2, 3, 0, 1, xoptions=gtk.FILL, yoptions=gtk.FILL)
        self.table.attach(self.trackstatus, 2, 3, 1, 2)

        self.buttonbar = gtk.HButtonBox()
        self.buttonbar.set_border_width(0)
        self.buttonbar.set_spacing(10)
        self.buttonbar.set_layout(gtk.BUTTONBOX_END)
        
        self.button = gtk.Button("Run Calibration")
        self.button.connect("clicked",self.on_calib_button_clicked)
        self.button.set_sensitive(False)


        self.button2 = gtk.Button("Continue to stimulus")                   # button added: 
        self.button2.connect("clicked",self.destroy)                        # it will destroy the eyetracker browser and
        self.button2.set_sensitive(True)                                    # then the program will continue to the stimulus

        # self.button3 = gtk.Button("EXIT")                                   # button added: 
        # self.button3.connect("clicked",self.exit_all)                          # it will destroy the eyetracker browser and
        # self.button3.set_sensitive(True)                                    # then the program will continue to the stimulus
        
        self.buttonbar.add(self.button)
        self.buttonbar.add(self.button2)
        # self.buttonbar.add(self.button3)
        
        self.eyetracker_label = gtk.Label()
        self.eyetracker_label.set_markup("<b>No eyetracker selected (double-click to choose).</b>")
        self.eyetracker_label.set_alignment(0.0, 0.5)
        self.table.attach(self.eyetracker_label, 0, 2, 2, 3, xoptions=gtk.FILL, yoptions=gtk.FILL)
        self.table.attach(self.buttonbar, 2, 3, 2, 3, xoptions=gtk.FILL, yoptions=gtk.FILL)

        self.window.add(self.table)
        self.window.show_all()
        
        # Setup Eyetracker stuff  
        tobii.eye_tracking_io.init()      
        self.mainloop_thread = tobii.eye_tracking_io.mainloop.MainloopThread()
        self.browser = tobii.eye_tracking_io.browsing.EyetrackerBrowser(self.mainloop_thread, lambda t, n, i: glib_idle_add(self.on_eyetracker_browser_event, t, n, i))

    def exit_all(self,widget):
        self.eyetracker = None
        self.calibplot.set_eyetracker(None)
        self.trackstatus.set_eyetracker(None)
        self.browser.stop()
        self.browser = None
        gtk.main_quit()
        sys.exit()


    def row_activated(self, treeview, path, user_data=None):
        # When an eyetracker is selected in the browser list we create a new 
        # eyetracker object and set it as the active one
        model = treeview.get_model()
        iter = model.get_iter(path)
        self.button.set_sensitive(False)
        self.trackstatus.set_eyetracker(None)
        self.calibplot.set_eyetracker(None)
        
        self.eyetracker_info = self.eyetrackers[model.get_value(iter, 0)]
        print "Connecting to:", self.eyetracker_info
        tobii.eye_tracking_io.eyetracker.Eyetracker.create_async(self.mainloop_thread,
                                                     self.eyetracker_info,
                                                     lambda error, eyetracker: glib_idle_add(self.on_eyetracker_created, error, eyetracker))
        
    #def on_eyetracker_created(self, error, eyetracker, eyetracker_info):
    def on_eyetracker_created(self, error, eyetracker):
        if error:
            print "  Connection to %s failed because of an exception: %s" % (self.eyetracker_info, error)
            if error == 0x20000402:
                show_message_box(parent=self.window, message="The selected unit is too old, a unit which supports protocol version 1.0 is required.\n\n<b>Details:</b> <i>%s</i>" % error)
            else:    
                show_message_box(parent=self.window, message="Could not connect to %s" % (self.eyetracker_info))
            return False
        
        self.eyetracker = eyetracker
        
        try:
            self.trackstatus.set_eyetracker(self.eyetracker)
            self.calibplot.set_eyetracker(self.eyetracker)
            self.button.set_sensitive(True)
            self.eyetracker_label.set_markup("<b>Connected to Eyetracker: %s</b>" % (self.eyetracker_info))
            print "   --- Connected!"
        except Exception, ex:
            print "  Exception occured: %s" %(ex)
            show_message_box(parent=self.window, message="An error occured during initialization of track status or fetching of calibration plot: %s" % (ex))
        return False

    def on_eyetracker_upgraded(self, error, protocol):
        try:
            self.trackstatus.set_eyetracker(self.eyetracker)
            self.calibplot.set_eyetracker(self.eyetracker)
            self.button.set_sensitive(True)
            self.eyetracker_label.set_markup("<b>Connected to Eyetracker: %s</b>" % (self.eyetracker_info))
            print "   --- Connected!"
        except Exception, ex:
            print "  Exception occured: %s" %(ex)
            show_message_box(parent=self.window, message="An error occured during initialization of track status or fetching of calibration plot: %s" % (ex))
        return False
    
    def on_calib_button_clicked(self, button):
        # Start the calibration procedure
        if self.eyetracker is not None:
            self.calibration = MyCalibration()
            if self.calibration.runCalibration(self.eyetracker):
                self.on_calib_done(1, '')
            else:
                self.on_calib_done(0, 'Calibration not succesful')
                print 'calibration returned False'
            

    
    def close_dialog(self, dialog, response_id):
        dialog.destroy()
    
    def on_calib_done(self, status, msg):
        # When the calibration procedure is done we update the calibration plot
        print 'calib done, show plot'
        if not status:
            show_message_box(parent=self.window, message=msg)
            pass
        
        self.calibplot.set_eyetracker(self.eyetracker)
        self.calibration = None
        return False

    def on_eyetracker_browser_event(self, event_type, event_name, ei):
        # When a new eyetracker is found we add it to the treeview and to the 
        # internal list of eyetracker_info objects
        if event_type == tobii.eye_tracking_io.browsing.EyetrackerBrowser.FOUND:
            self.eyetrackers[ei.product_id] = ei
            self.liststore.append(('%s' % ei.product_id, ei.model, ei.status))
            return False
        
        # Otherwise we remove the tracker from the treeview and the eyetracker_info list...
        del self.eyetrackers[ei.product_id]
        iter = self.liststore.get_iter_first()
        while iter is not None:
            if self.liststore.get_value(iter, 0) == str(ei.product_id):
                self.liststore.remove(iter)
                break
            iter = self.liststore.iter_next(iter)
        
        # ...and add it again if it is an update message
        if event_type == tobii.eye_tracking_io.browsing.EyetrackerBrowser.UPDATED:
            self.eyetrackers[ei.product_id] = ei
            self.liststore.append([ei.product_id, ei.model, ei.status])
        return False
        

    def delete_event(self, widget, event, data=None):
        # Change FALSE to TRUE and the main window will not be destroyed
        # with a "delete_event".
        return False

    def destroy(self, widget, data=None):
        self.eyetracker = None
        self.calibplot.set_eyetracker(None)
        self.trackstatus.set_eyetracker(None)
        self.browser.stop()
        self.browser = None
        gtk.main_quit()

    def main(self):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.gdk.threads_init()
        gtk.main()
        self.mainloop_thread.stop()


######################################################
## Adapted from PyGaze
######################################################

class MyTobiiController:
    
    def __init__(self,datafilename='eyetrackeroutputdatafile.txt', parameters = None):
        
        """Initializes TobiiController instance
        
        arguments
        disp        --  a libscreen.Display instance
        
        keyword arguments
        None
        """
        
        self.filename   = datafilename
        self.parameters = parameters

        self.codes = [1, 4, 8, 999]
        
        # eye tracking
        self.eyetracker = None
        self.eyetrackers = {}
        self.gazeData = []
        self.eventData = []
        self.datafile = None

        # input events data struct
        self.input_events = []                                              #
        
        # initialize communications
        tobii.eye_tracking_io.init()
        self.clock = tobii.eye_tracking_io.time.clock.Clock()
        self.mainloop_thread = tobii.eye_tracking_io.mainloop.MainloopThread()
        self.browser = tobii.eye_tracking_io.browsing.EyetrackerBrowser(self.mainloop_thread, lambda t, n, i: self.on_eyetracker_browser_event(t, n, i))
        self.mainloop_thread.start()        # SDK's example Eyetracker browser does not start this mainloop

    def waitForFindEyeTracker(self):
        
        """Keeps running until an eyetracker is found
        
        arguments
        None
        
        keyword arguments
        None
        
        returns
        None        --  only returns when an entry has been made to the
                    self.eyetrackers dict
        """
        
        while len(self.eyetrackers.keys())==0:
            pass
        
    def on_eyetracker_browser_event(self, event_type, event_name, eyetracker_info):
        
        """Adds a new or updates an existing tracker to self.eyetrackers,
        if one is available
        
        arguments
        event_type      --  a tobii.eye_tracking_io.browsing.EyetrackerBrowser
                        event
        event_name      --  don't know what this is for; probably passed
                        by some underlying Tobii function, specifying
                        a device name; it's not used within this
                        function
        eyetracker_info --  a struct containing information on the eye
                        tracker (e.g. it's product_id)
        
        keyword arguments
        None
        
        returns
        False           --  returns False after adding a new tracker to
                        self.eyetrackers or after deleting it
        """
        
        # When a new eyetracker is found we add it to the treeview and to the 
        # internal list of eyetracker_info objects
        
        if event_type == tobii.eye_tracking_io.browsing.EyetrackerBrowser.FOUND:
            self.eyetrackers[eyetracker_info.product_id] = eyetracker_info
            return False
        
        # Otherwise we remove the tracker from the treeview and the eyetracker_info list...
        del self.eyetrackers[eyetracker_info.product_id]
        
        # ...and add it again if it is an update message
        if event_type == tobii.eye_tracking_io.browsing.EyetrackerBrowser.UPDATED:
            self.eyetrackers[eyetracker_info.product_id] = eyetracker_info
        return False

    
    # activation methods ---------------------------------------------------------------------

    def activate(self,eyetracker):
        
        """Connects to specified eye tracker
        
        arguments
        eyetracker  --  key for the self.eyetracker dict under which the
                    eye tracker to which you want to connect is found
        
        keyword arguments
        None
        
        returns
        None        --  calls TobiiController.on_eyetracker_created, then
                    sets self.syncmanager
        """
        
        eyetracker_info = self.eyetrackers[eyetracker]
        print "MyTobiiController connecting to:", eyetracker_info
        tobii.eye_tracking_io.eyetracker.Eyetracker.create_async(self.mainloop_thread,
                                                     eyetracker_info,
                                                     lambda error, eyetracker: self.on_eyetracker_created(error, eyetracker, eyetracker_info))
        
        while self.eyetracker==None:
            pass
        self.syncmanager = tobii.eye_tracking_io.time.sync.SyncManager(self.clock,eyetracker_info,self.mainloop_thread)

    def on_eyetracker_created(self, error, eyetracker, eyetracker_info):
        
        """Function is called by TobiiController.activate, to handle all
        operations after connecting to a tracker has been succesfull
        
        arguments
        error           --  some Tobii error message
        eyetracker      --  key for the self.eyetracker dict under which
                        the eye tracker that is currently connected
        eyetracker_info --  name of the eye tracker to which a
                        connection has been established
        
        keyword arguments
        None
        
        returns
        None or False   --  returns nothing and sets self.eyetracke on
                        connection success; returns False on failure
        """
        if error:
            print("WARNING! libtobii.TobiiController.on_eyetracker_created: Connection to %s failed because of an exception: %s" % (eyetracker_info, error))
            if error == 0x20000402:
                print("WARNING! libtobii.TobiiController.on_eyetracker_created: The selected unit is too old, a unit which supports protocol version 1.0 is required.\n\n<b>Details:</b> <i>%s</i>" % error)
            else:
                print("WARNING! libtobii.TobiiController.on_eyetracker_created: Could not connect to %s" % (eyetracker_info))
            return False
        
        self.eyetracker = eyetracker

    def destroy(self):
        
        """Removes eye tracker and stops all operations
        
        arguments
        None
        
        keyword arguments
        None
        
        returns
        None        --  sets self.eyetracker and self.browser to None;
                    stops browser and the 
                    tobii.eye_tracking_io.mainloop.MainloopThread
        """

        self.eyetracker = None
        self.browser.stop()
        self.browser = None
        self.mainloop_thread.stop()

    def startTracking(self):
        
        """Starts the collection of gaze data
        
        arguments
        None
        
        keyword arguments
        None
        
        returns
        None        --  resets both self.gazeData and self.eventData, then
                    sets TobiiTracker.on_gazedata as an event callback
                    for self.eyetracker.events.OnGazeDataReceived and
                    calls self.eyetracker.StartTracking()
        """
        # self.starttimeET = self.syncmanager.convert_from_local_to_remote(self.clock.get_time())     # JL
        self.starttimeET = self.clock.get_time()
        self.starttimePY = time.time()                                                              # JL
        
        self.gazeData = []
        self.eventData = []
        self.eyetracker.events.OnGazeDataReceived += self.on_gazedata
        self.eyetracker.StartTracking()

    def stopTracking(self):
        
        """Starts the collection of gaze data
        
        arguments
        None
        
        keyword arguments
        None
        
        returns
        None        --  calls self.eyetracker.StopTracking(), then unsets
                    TobiiTracker.on_gazedata as an event callback for 
                    self.eyetracker.events.OnGazeDataReceived, and
                    calls TobiiTracker.flushData before resetting both
                    self.gazeData and self.eventData
        """
        self.eyetracker.StopTracking()
        self.eyetracker.events.OnGazeDataReceived -= self.on_gazedata
        # self.flushData()
        # self.write_eyetracker_data_file()
        # self.write_vergence_data_file()
        self.compute_event_code()
        # self.compute_validity_percentage()
        self.write_eyetracker_data_file()
        self.gazeData = []
        self.eventData = []

    def on_gazedata(self,error,gaze):
        
        """Adds new data point to the data collection (self.gazeData)
        
        arguments
        error       --  some Tobii error message, isn't used in function
        gaze        --  Tobii gaze data struct
        
        keyword arguments
        None
        
        returns
        None        --  appends gaze to self.gazeData list
        """
        self.gazeData.append(gaze)


    # calibration methods (we do not use these at the moment) ------------------------------

    def performCalibration(self):
        print 'in performCalibration'
        if self.eyetracker is not None:
            self.calibration = Calibration()
            print '---------------before gtk main--------------------'
            # gtk.main()
            print '---------------after gtk main--------------------'
            # self.calibration.runCalibration(self.eyetracker, lambda status, message: glib_idle_add(self.on_calib_done, status, message))
            self.calibration.run(self.eyetracker, lambda status, message: glib_idle_add(self.on_calib_done, status, message))
        else:
            print 'eyetracker is None'

        # calibration = Calibration()
        # calibration.run(self.eyetracker, lambda status, message: glib_idle_add(self.on_calib_done, status, message))

    def on_calib_done(self, status, msg):
        # When the calibration procedure is done we update the calibration plot
        if not status:
            # show_message_box(parent=self.window, message=msg)
            pass
        print 'on calib done'
        print status
        # self.calibplot.set_eyetracker(self.eyetracker)
        # self.calibration = None
        # return False


    # get data methods ---------------------------------------------------------------------

    def getGazePosition(self,gaze):
        
        """Extracts the gaze positions of both eyes from the Tobii gaze
        struct and recalculates them to PyGaze coordinates
        
        arguments
        gaze        --  Tobii gaze struct
        
        keyword arguments
        None
        
        returns
        gazepos --  a (Lx,Ly,Rx,Ry) tuple for the gaze positions
                    of both eyes
        """
        
        return ((gaze.LeftGazePoint2D.x),
                (gaze.LeftGazePoint2D.y),
                (gaze.RightGazePoint2D.x),
                (gaze.RightGazePoint2D.y))
    
    def getCurrentGazePosition(self):
        
        """Provides the newest gaze position sample
        
        arguments
        None
        
        keyword arguments
        None
        
        returns
        gazepos --  a (Lx,Ly,Rx,Ry) tuple for the gaze positions
                    of both eyes or (None,None,None,None) if no new
                    sample is available
        """
        
        if len(self.gazeData)==0:
            return (None,None,None,None)
        else:
            return self.getGazePosition(self.gazeData[-1])

    
    # write data methods ---------------------------------------------------------------------

    def OLD_write_eyetracker_data_file(self):
        # def write_eyetracker_data_file(self,filename='eyetrackeroutputdatafile.txt'):
        """
        Uses the complete GazeData array from tobii.controller.
        Based on the libtobii.TobiiController's flushData() method
        """
        if self.gazeData == []:
            print 'gazeData is empty'
            return

        GazeData = self.gazeData            # get stored GazeData

        # To do: create filename (different each time)

        # fields in header
        fields = ['Timestamp','LeftEyePosition3D.x','LeftEyePosition3D.y','LeftEyePosition3D.z',
                    'LeftEyePosition3DRelative.x','LeftEyePosition3DRelative.y','LeftEyePosition3DRelative.z',
                    'LeftGazePoint2D.x','LeftGazePoint2D.y','LeftGazePoint3D.x','LeftGazePoint3D.y',
                    'LeftGazePoint3D.z','LeftPupil','LeftValidity','RightEyePosition3D.x','RightEyePosition3D.y',
                    'RightEyePosition3D.z','RightEyePosition3DRelative.x','RightEyePosition3DRelative.y',
                    'RightEyePosition3DRelative.z','RightGazePoint2D.x','RightGazePoint2D.y','RightGazePoint3D.x',
                    'RightGazePoint3D.y','RightGazePoint3D.z','RightPupil','RightValidity']
        
        timeStampStart = GazeData[0].Timestamp          # time of the first event

        with open(self.filename, 'a' ) as f:            # open or create text file 'filename' to append             
            f.write('\t'.join(fields)+'\n')             # write header. Separate the fields into tabs

            for g in GazeData:
                # write timestamp and gaze position for both eyes to the datafile
                # f.write('%.1f\t%.4f\t%.4f\t%d\t%.4f\t%.4f\t%d'%(
                f.write('%.1f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%d\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%d\t'%(

                                    (g.Timestamp-timeStampStart)/1000.0,

                                    g.LeftEyePosition3D.x,
                                    g.LeftEyePosition3D.y,
                                    g.LeftEyePosition3D.z,

                                    g.LeftEyePosition3DRelative.x,  
                                    g.LeftEyePosition3DRelative.y,
                                    g.LeftEyePosition3DRelative.z,

                                    g.LeftGazePoint2D.x,
                                    g.LeftGazePoint2D.y,

                                    g.LeftGazePoint3D.x,
                                    g.LeftGazePoint3D.y,
                                    g.LeftGazePoint3D.z,

                                    g.LeftPupil,

                                    g.LeftValidity,

                                    g.RightEyePosition3D.x,
                                    g.RightEyePosition3D.y,
                                    g.RightEyePosition3D.z,

                                    g.RightEyePosition3DRelative.x,
                                    g.RightEyePosition3DRelative.y,
                                    g.RightEyePosition3DRelative.z,

                                    g.RightGazePoint2D.x,
                                    g.RightGazePoint2D.y,

                                    g.RightGazePoint3D.x,
                                    g.RightGazePoint3D.y,
                                    g.RightGazePoint3D.z,

                                    g.RightPupil,           

                                    g.RightValidity,

                                    )
                )

                f.write('\n')

            
            # general format of an event string
            # formatstr = '%.1f'+'\t'*9+'%s\n'
            formatstr = '%.1f'+'\t'+'%s\n'
        
            # write all events to the datafile, using the formatstring
            for e in self.eventData:
                f.write(formatstr % ((e[0]-timeStampStart)/1000.0,e[1]))

        os.chmod(self.filename,stat.S_IREAD) # make file read only


        pass


    def write_eyetracker_data_file(self):
        # def write_eyetracker_data_file(self,filename='eyetrackeroutputdatafile.txt'):
        """
        Uses the complete GazeData array from tobii.controller.
        Based on the libtobii.TobiiController's flushData() method
        """
        import itertools

        if self.gazeData == []:
            print 'gazeData is empty'
            return



        # fields in header
        fields = ['Timestamp','LeftEyePosition3D.x','LeftEyePosition3D.y','LeftEyePosition3D.z',
                    'LeftEyePosition3DRelative.x','LeftEyePosition3DRelative.y','LeftEyePosition3DRelative.z',
                    'LeftGazePoint2D.x','LeftGazePoint2D.y','LeftGazePoint3D.x','LeftGazePoint3D.y',
                    'LeftGazePoint3D.z','LeftPupil','LeftValidity','RightEyePosition3D.x','RightEyePosition3D.y',
                    'RightEyePosition3D.z','RightEyePosition3DRelative.x','RightEyePosition3DRelative.y',
                    'RightEyePosition3DRelative.z','RightGazePoint2D.x','RightGazePoint2D.y','RightGazePoint3D.x',
                    'RightGazePoint3D.y','RightGazePoint3D.z','RightPupil','RightValidity', 
                    'EventTimeStamp','EventType', 'EventId', 'EventValue'] # these last line is added (see OLD_write_eyetracker_data_file)

        timeStampStart = self.gazeData[0].Timestamp          # time of the first event
        formatstr = '%.1f'+'\t'+'%s'                  # format for events


        with open(self.filename, 'a' ) as f:            # open or create text file 'filename' to append             
            f.write('\t'.join(fields)+'\n')             # write header. Separate the fields into tabs

            # for g in GazeData:
            for g, e in itertools.izip_longest(self.gazeData,self.eventData):
                # write timestamp and gaze position for both eyes to the datafile
                # f.write('%.1f\t%.4f\t%.4f\t%d\t%.4f\t%.4f\t%d'%(
                f.write('%.1f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%d\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%d\t'%(

                                    (g.Timestamp-timeStampStart)/1000.0,

                                    g.LeftEyePosition3D.x,
                                    g.LeftEyePosition3D.y,
                                    g.LeftEyePosition3D.z,

                                    g.LeftEyePosition3DRelative.x,  
                                    g.LeftEyePosition3DRelative.y,
                                    g.LeftEyePosition3DRelative.z,

                                    g.LeftGazePoint2D.x,
                                    g.LeftGazePoint2D.y,

                                    g.LeftGazePoint3D.x,
                                    g.LeftGazePoint3D.y,
                                    g.LeftGazePoint3D.z,

                                    g.LeftPupil,

                                    g.LeftValidity,

                                    g.RightEyePosition3D.x,
                                    g.RightEyePosition3D.y,
                                    g.RightEyePosition3D.z,

                                    g.RightEyePosition3DRelative.x,
                                    g.RightEyePosition3DRelative.y,
                                    g.RightEyePosition3DRelative.z,

                                    g.RightGazePoint2D.x,
                                    g.RightGazePoint2D.y,

                                    g.RightGazePoint3D.x,
                                    g.RightGazePoint3D.y,
                                    g.RightGazePoint3D.z,

                                    g.RightPupil,           

                                    g.RightValidity,



                                    )
                )

                # write events:
                if e is not None:
                    f.write(formatstr % ((e[0]-timeStampStart)/1000.0,e[1]))
                else:
                    f.write('-\t-\t-\t-')    # the method that reads it needs the data to be uniform

                f.write('\n')

            
            # # general format of an event string
            # # formatstr = '%.1f'+'\t'*9+'%s\n'
            # formatstr = '%.1f'+'\t'+'%s\n'
        
            # # write all events to the datafile, using the formatstring
            # for e in self.eventData:
            #     f.write(formatstr % ((e[0]-timeStampStart)/1000.0,e[1]))

        os.chmod(self.filename,stat.S_IREAD) # make file read only


        pass


    def write_vergence_data_file(self):

        # fields in header
        fields = ['Timestamp','LeftGazePoint2D.x','RightGazePoint2D.x','Vergence', 'FixationDist']

        timeStampStart = self.gazeData[0].Timestamp     # time of the first event


        with open(self.filenamev, 'w' ) as f:            # open or create text file 'filename' to append             
            f.write('\t'.join(fields)+'\n')             # write header. Separate the fields into tabs

            # for g in GazeData:
            for g in self.gazeData:
                SL = float(g.LeftGazePoint2D.x)
                SR = float(g.RightGazePoint2D.x)

                verg, fixdist = self.calcVerg(SL, SR)

                # write timestamp and gaze position for both eyes to the datafile
                # f.write('%.1f\t%.4f\t%.4f\t%d\t%.4f\t%.4f\t%d'%(
                f.write('%.1f\t%.4f\t%.4f\t%.4f\t%.4f\t'%(

                                    (g.Timestamp-timeStampStart)/1000.0,

                                    g.LeftGazePoint2D.x,

                                    g.RightGazePoint2D.x,

                                    verg,

                                    fixdist,

                                    )
                )

                f.write('\n')
            
        os.chmod(self.filenamev,stat.S_IREAD) # make file read only


        pass
        pass

    def calcVerg(self, SL, SR, SL2 = 0.243, SR2 = 0.240, scrnWidth_cm = 31.1, pd = 0.06, b = 0.6, So = 0.5):
        """
        Input: SL (left gaze pos), SR (right gaze pos), scrnWidth_cm of monitor, interpupillary distance (IPD) in meters,
        b (monitor distance), So (value of midpoint of screen in arbitrary units) 
        Output:
        """
        from math import atan
        from math import degrees
        ##### converting input values ######

        pdhalf = pd/2               # half IPD in m
        dc = 0.013                  # distance between corneal vertex and center of eye (see De Luca et al 2009) in m
        d = b + dc                  # distance between screen plane and center of eye in m
        
        scrnWidth = scrnWidth_cm/100 # scrnWidth in meter units
        So = So * scrnWidth         # convert midpoint value from arbitrary to meter units 

        SL = SL * scrnWidth         # convert left gaze from arbitrary unit to meter units
        SR = SR * scrnWidth         # convert right gaze from arbitrary unit to meter units


        ##### derived values for vergence aligned to monitor #####
        
        Sm = (SL + SR)/2            # point of ideal vergence where SR coincides with SL (see Fig 1 De Luca, 2009)
        y = SL - SR                 # length of distance between SR and SL in m
        j = So - Sm                 # length of distance between center of screen and ideal vergence point



        ##### derived values for not-aligned vergence #####
        x = (d * y)/(pd + y)        # distance between fixation plane and screen; determined using similar triangles (see Eqn 8, Fig 3, De Luca, 2009)
        SLseg = SL - (So - pdhalf)  # 
        k = pdhalf-(SLseg*(d-x)/d)  # length of distance between center of screen and projected vergence point (similar to var j)(see eqn 10-12)



        ##### CALCULATE aligned vergence with version #####
        # ideal vergence: when y = 0, and vergence is aligned to the distance of computer monitor
        # version: when j is not equal to 0, in other words, the vergence point(Sm) is not equal to the center of the screen(So)

        # print('ideal verg is ', degrees(atan((pdhalf-j)/d) + atan((pdhalf+j)/d)))
        idealv = degrees(atan((pdhalf-j)/d) + atan((pdhalf+j)/d))


        ##### CALCULATE not-aligned vergence with version #####
        # dynamic vergence: when y is not equal to 0
        # version: when j is not equal to 0, as is the case for ideal vergence with version

        # print('not-aligned verg is ', degrees( atan((pdhalf-k)/(d-x)) + atan((pdhalf+k)/(d-x)) ))
        noalignedv = degrees( atan((pdhalf-k)/(d-x)) + atan((pdhalf+k)/(d-x)) )

        ##### RETURN: not-aligned vergance and distance 


        return noalignedv, (d-x)

    def write_eyetracker_data_file(self):
        """
        Uses the complete GazeData array from tobii.controller.
        Based on the libtobii.TobiiController's flushData() method
        """
        import itertools                                                    # to iterate over multiple lists

        if self.gazeData == []:
            print 'gazeData is empty'
            return

        timeStampStart = self.gazeData[0].Timestamp                         # time of the first "eye" event
        ntrials = int(self.parameters['numtrials'])                         # get number of trials

        # fields in header
        fields = ['Timestamp','LeftEyePosition3D.x','LeftEyePosition3D.y','LeftEyePosition3D.z',
                    'LeftEyePosition3DRelative.x','LeftEyePosition3DRelative.y','LeftEyePosition3DRelative.z',
                    'LeftGazePoint2D.x','LeftGazePoint2D.y','LeftGazePoint3D.x','LeftGazePoint3D.y',
                    'LeftGazePoint3D.z','LeftPupil','LeftValidity','RightEyePosition3D.x','RightEyePosition3D.y',
                    'RightEyePosition3D.z','RightEyePosition3DRelative.x','RightEyePosition3DRelative.y',
                    'RightEyePosition3DRelative.z','RightGazePoint2D.x','RightGazePoint2D.y','RightGazePoint3D.x',
                    'RightGazePoint3D.y','RightGazePoint3D.z','RightPupil','RightValidity', 
                    'Vergence','FixationDist','EventTimeStamp','EventName','EventType', 'EventId', 'Code',
                    'Parameters'] # these last line is added (see OLD_write_eyetracker_data_file)
        
        for n in range(ntrials):                                            # for each trial
            fields.append('Value for trial {0}'.format(n+1))                # add field in header 


        with open(self.filename, 'a' ) as f:                                # open or create text file 'filename' to append             
            f.write('\t'.join(fields)+'\n')                                 # write header. Separate the fields into tabs

            # for g in GazeData:
            for g, e, p in itertools.izip_longest(self.gazeData,self.input_events, self.parameters.items()):

                SL = float(g.LeftGazePoint2D.x)                             # get X left gaze point 
                SR = float(g.RightGazePoint2D.x)                            # get X right gaze point
                
                if g.LeftValidity == g.RightValidity:                       # if both validity values are the same,
                    verg, fixdist = self.calcVerg(SL, SR)                   # compute vergence and fixation distance
                else:                                                       # if validity values are not the same,
                    verg, fixdist = -1, -1                                  # set vergence and fix dist to -1 (for now)

                # write eyetracker data
                f.write('%.1f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%d\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%d\t%.4f\t%.4f\t'%(

                                    (g.Timestamp-timeStampStart)/1000.0,

                                    g.LeftEyePosition3D.x,
                                    g.LeftEyePosition3D.y,
                                    g.LeftEyePosition3D.z,

                                    g.LeftEyePosition3DRelative.x,  
                                    g.LeftEyePosition3DRelative.y,
                                    g.LeftEyePosition3DRelative.z,

                                    g.LeftGazePoint2D.x,
                                    g.LeftGazePoint2D.y,

                                    g.LeftGazePoint3D.x,
                                    g.LeftGazePoint3D.y,
                                    g.LeftGazePoint3D.z,

                                    g.LeftPupil,

                                    g.LeftValidity,

                                    g.RightEyePosition3D.x,
                                    g.RightEyePosition3D.y,
                                    g.RightEyePosition3D.z,

                                    g.RightEyePosition3DRelative.x,
                                    g.RightEyePosition3DRelative.y,
                                    g.RightEyePosition3DRelative.z,

                                    g.RightGazePoint2D.x,
                                    g.RightGazePoint2D.y,

                                    g.RightGazePoint3D.x,
                                    g.RightGazePoint3D.y,
                                    g.RightGazePoint3D.z,

                                    g.RightPupil,           

                                    g.RightValidity,

                                    verg,
                                    fixdist,



                                    )
                )

                # write events
                if e is not None:                                           # if event is not None,
                    f.write('{0}\t{1}\t{2}\t{3}\t{4}\t'.format(             # write to file 
                        (e.ETtime - timeStampStart)/1000.0,                 # its timestamp
                        e.name, e.type, e.id, e.code))                      # name, type, id and code.
                else:                                                       # if there are no more events, fill rows with '-'
                    f.write('-\t-\t-\t-\t-\t')                              # because the method that reads the data needs it to be uniform

                # write parameters
                if p is not None:                                           # if p (each pair of (key, value) in parameters dict) is not None
                    k, v = p[0], p[1]                                       # get k and v (key and value)
                    f.write('{0}'.format(k))                                # write key (name of parameter)
                    if type(v) in (int, float, str) or 'color' in k:        # If it is a config parameter,
                        for i in range(ntrials):                            # write it (value will repeat
                            f.write('\t{0}'.format(v))                      # for each trial column).
                    else:                                                   # If it is a trial parameter
                        for i in range(ntrials):                            # write the value
                            f.write('\t{0}'.format(v[i]))                   # for each trial.
                else:                                                       # when there are no more parameters
                    f.write('-\t'*(ntrials+1))                              # fill columns with '-'

                f.write('\n')                                               # write end of line

        os.chmod(self.filename,stat.S_IREAD)                                # make file read only


        pass


    # Events functions ---------------------------------------------------------------------

    def recordEvent(self,event):
        
        """Adds an event to the event data
        
        arguments
        event       --  a string containing an event description
        
        keyword arguments
        None
        
        returns
        None        --  appends a (timestamp,event) tuple to
                    self.eventData
        """
        
        t = self.syncmanager.convert_from_local_to_remote(self.clock.get_time())
        self.eventData.append((t,event))

    def myRecordEvent(self, name = '', lastevent = None, intype = '', inid = ''):
        t = self.syncmanager.convert_from_local_to_remote(self.clock.get_time())
        timenowEY = self.clock.get_time()
        timenowPY = time.time()


        # print t, self.starttimeET


        if name == 'InputEvent':
            self.input_events.append(EventItem(name = name, timestamp = t, etype = lastevent.type, eid = lastevent.id))

            # print 'Input event. ET time is {0}, time.time() is {1}. difference: {2}'.format(
                # (timenowEY - self.starttimeET)/1000000.0, timenowPY - self.starttimePY, (timenowEY - self.starttimeET)/1000000.0 - (timenowPY - self.starttimePY))
        
        elif name == 'TrialEvent':
            # self.input_events.append(EventItem(name = name, timestamp = t, etype = intype, eid = (inid - self.gazeData[0].Timestamp)/1000.0))
            self.input_events.append(EventItem(name = name, timestamp = t, etype = intype, eid = (t - self.gazeData[0].Timestamp)/1000.0))

            pass

        else:
            self.input_event.append(EventItem(name = 'otherEvent', timestamp = t, etype = 'None', eid = 'None'))
    
    def myRecordEvent2(self, event = None):
        t = self.syncmanager.convert_from_local_to_remote(self.clock.get_time())
        # t = self.syncmanager.convert_from_local_to_remote(event.timestamp)
        event.ETtime = t
        self.input_events.append(event)

    def compute_event_code(self):
        right_keys  = [4, 109, 110, 106]
        left_keys   = [1, 122, 120, 115]
        for e in self.input_events:
            # compute code
            if e.name == 'InputEvent':

                isdown  = 'DW' in e.type
                isup    = 'UP' in e.type
                               
                if   (e.id in right_keys) and (isdown):
                    e.code = self.codes[1]
                    pass
                
                elif (e.id in right_keys) and (isup):
                    e.code = -self.codes[1]
                
                elif (e.id in left_keys) and (isdown):
                    e.code = self.codes[0]
                    pass
                
                elif (e.id in left_keys) and (isup):
                    e.code = -self.codes[0]
                
                else: # key not in right and left arrays
                    e.code = self.codes[3]

            elif e.name == 'TrialEvent':
                # code = 8 if e.id == 'START' else -8
                e.code = 8 if 'START' in e.id else -8
            pass

        pass

    def compute_validity_percentage(self):
        
        # from input_events get trial events
        trial_ts        = [e.ETtime for e in self.input_events if e.code in (8, -8)]
        et_ts           = [g.Timestamp for g in self.gazeData]
        leftvalidity    = [g.LeftValidity for g in self.gazeData]
        rightvalidity   = [g.RightValidity for g in self.gazeData]

        it = 0
        for trial in range(len(trial_ts)/2):                                   # for each trial
            start = trial_ts[it]                                                       # timestamp start of trial
            end   = trial_ts[it+1]                                                     # timestamp end of trial

            # get row index
            val, idx_start = find_nearest_above(et_ts, start)
            val, idx_end   = find_nearest_above(et_ts, end)

            nsamples = idx_end - idx_start

            lv_trial = 100 * (leftvalidity[idx_start:idx_end] == 4).sum()/float(nsamples)  # left eye:  % of lost data
            rv_trial = 100 * (rightvalidity[idx_start:idx_end] == 4).sum()/float(nsamples)  # right eye: % of lost data

            print 'For trial {0}, {1} % of data was lost'.format(trial+1, "%.1f" % lv_trial)    # (e.g. validity equal to 4)

            it += 1 

    
    # My calibration methods ---------------------------------------------------------------------
    
    def runCalibration(self):
        # if self.verbose: print 'mycalibration - run'

        self._lastCalibrationOK=False
        self._lastCalibrationReturnCode=0
        self._lastCalibration=None
        self.point_index = -1

        calibration_sequence_completed=False
        
        if hasattr(self.eyetracker,'ClearCalibration'):
            print 'clear previous calibration'
            self.eyetracker.ClearCalibration()

        
        MyWin = Window(fullscreen=True, visible = 0)

        # self.on_calib_done = on_calib_done
        
        lastevent = LastEvent()                                             # LastEvent() is defined in rlabs_libutils
        win_size = MyWin.get_size()

        p = Point2D()
        points = [(0.1,0.1), (0.9,0.1) , (0.5,0.5), (0.1,0.9), (0.9,0.9)]
        shuffle(points)

        fg_color = (0.88,0.88,0.88)


        instuction_text="Press SPACE to Start Calibration; ESCAPE to Exit."
        mylabel = pyglet.text.Label(instuction_text, font_name = 'Arial', font_size = 36, x = MyWin.width/2, 
            y = MyWin.height/2, multiline = True, width=600, anchor_x = "center", anchor_y = "center")

        MyWin.set_visible(True)


        ######################################################
        ## SHOW WELCOME FOR CALIBRATION
        ######################################################
        while not MyWin.has_exit:                                           # Show welcome text for calibration
            
            ## CHECK INPUT
            lastevent = my_dispatch_events(MyWin, lastevent)                # my_dispatch_events is defined in rlabs_libutils
            if lastevent.type != []:                                        # check if last event is SPACE or ...
                if lastevent.id == 32 and lastevent.type == "Key_UP":       # if it is space, break while loop
                    lastevent.reset_values()                                # reset values of event

                    continue_calibration = True

                    break

                if lastevent.id == 27 and lastevent.type == "Key_UP":       # if it is escape, return false
                    lastevent.reset_values()                                # reset values of event
                    continue_calibration = False
                
                # if not continue_calibration:
                    # return False
            
            ## DISPLAY TEXT
            MyWin.clear()                                                   # clear window
            MyWin.dispatch_events()                                         # dispatch window events (very important call)
            mylabel.draw()                                                  # show message
            MyWin.flip()                                                    # flip window

            pass


        ######################################################
        ## CALIBRATION LOOP
        ######################################################
        self.eyetracker.StartCalibration(self.on_start_calibration)                                     # start calibration

        for point in points:                                                    # for each point

            p_scaled = []
            p_scaled.append(point[0] * MyWin.width)                             # range horizontal coordinate to pyglet window
            p_scaled.append(MyWin.height - point[1] * MyWin.height)             # range vertical coordinate to pyglet window
                       
            while not MyWin.has_exit:                                           # show point

                glClearColor(fg_color[0],fg_color[1],fg_color[2],1)             # set background color
                MyWin.clear()                                                   # clear window
                MyWin.dispatch_events()                                         # dispatch window events (very important call)

                ######################################################
                ## CHECK INPUT
                ######################################################
                lastevent = my_dispatch_events(MyWin, lastevent)                # my_dispatch_events is defined in rlabs_libutils
                if lastevent.type != []:                                        # check if last event is SPACE BAR or ...
                    if lastevent.id == 32 and lastevent.type == "Key_UP":       # if it is space
                        lastevent.reset_values()                                # reset values of event
                        break

                ######################################################  
                ## Draw point
                ######################################################
                drawCircle(p_scaled[0], p_scaled[1], radius = 10, circle_color = (0,0,0))
                drawCircle(p_scaled[0], p_scaled[1], radius = 3, circle_color = (1,1,1))

                ######################################################  
                ## Flip the window
                ######################################################
                MyWin.flip()                                                    # flip window

                pass

            ######################################################  
            ## Add point to eyetracker (point not scaled)
            ######################################################
            p.x, p.y = point
            self.eyetracker.AddCalibrationPoint(p,self.on_add_calibration_point)                     # add calibration point to eyetracker
            time.sleep(0.5)            

            
            self.point_index += 1 
            print self.point_index, len(points)
            if self.point_index == (len(points)):                                                           # if last points
                calibration_sequence_completed=True                                                 # end calibration
            
            if MyWin.has_exit:                                                   # This breaks the For stimulus loop. 
                break

        if calibration_sequence_completed:
            print 'sequence completed'
            self.eyetracker.ComputeCalibration(self.on_compute_calibration)                             # compute calibration

        self.eyetracker.StopCalibration(None)
        print 'calibration done'

        if self._lastCalibrationOK is True:
            print '_lastCalibrationOK is True'
            # self._tobii.GetCalibration(self.on_calibration_result)
            # calibration_result = self.eyetracker.GetCalibration(self.on_calibration_result)
            pass

        if self._lastCalibrationOK is False:
            print '_lastCalibrationOK is False'
            pass

        
        MyWin.close()

        return True


        pass

    def on_start_calibration(self,*args,**kwargs):
        pass
    
    def on_add_calibration_point(self,*args,**kwargs):
        pass

    def on_compute_calibration(self,*args,**kwargs):
        print 'on compute calibration'
        self._lastCalibrationReturnCode=args[0]
        if self._lastCalibrationReturnCode!=0:
            print2err("ERROR: Tobii Calibration Calculation Failed. Error code: {0}".format(self._lastCalibrationReturnCode))
            self._lastCalibrationOK=False
            # self._msg_queue.put("CALIBRATION_COMPUTATION_FAILED")
        
        else:
            # self._msg_queue.put("CALIBRATION_COMPUTATION_COMPLETE")
            self._lastCalibrationOK=True
            pass


######################################################
## Other functions
######################################################
def calibration_routine(MyWin,controller,testing_with_eyetracker=1):

    lastevent = LastEvent()                                                 # LastEvent() is defined in rlabs_libutils
    win_size = MyWin.get_size()
    
    points = [(0.1,0.1), (0.9,0.1) , (0.5,0.5), (0.1,0.9), (0.9,0.9)]

    fg_color = (0.88,0.88,0.88)
    shuffle(points)

    # textWelcome = "\t\t\t\tWelcome\n \t\t\tClick or SPACE\n \t\t\tto start"
    textWelcome = 'Calibration routine.\nPress SPACE for next point.\nPress SPACE to start.'
    mylabel = pyglet.text.Label(textWelcome, font_name = 'Arial', font_size = 36, x = MyWin.width/2, 
        y = MyWin.height/2, multiline = True, width=600, anchor_x = "center", anchor_y = "center")


    MyWin.set_visible(True)

    ######################################################
    ## INSTRUCTIONS FOR CALIBRATION
    ######################################################
    while not MyWin.has_exit:                                           # Show welcome text for calibration
        
        ## CHECK INPUT
        lastevent = my_dispatch_events(MyWin, lastevent)                # my_dispatch_events is defined in rlabs_libutils
        if lastevent.type != []:                                        # check if last event is SPACE BAR or ...
            if lastevent.id == 32 and lastevent.type == "Key_UP":       # if it is space, break while loop
                lastevent.reset_values()                                # reset values of event
                break
        
        ######################################################
        ## DISPLAY TEXT
        ######################################################
        MyWin.clear()                                                   # clear window
        MyWin.dispatch_events()                                         # dispatch window events (very important call)
        mylabel.draw()                                                  # show message
        MyWin.flip()                                                    # flip window

        pass

    if testing_with_eyetracker:
        controller.startTracking()                                          # start eye tracking
        time.sleep(0.2)                                                     # wait for the eytracker to warm up
        controller.recordEvent('calibration stim start')                     # write event to eyetracker data file
    ######################################################
    ## CALIBRATION LOOP
    ######################################################
    for point in points:                                                    # for each point

        p_scaled = []
        p_scaled.append(point[0] * MyWin.width)                             # range horizontal coordinate to pyglet window
        p_scaled.append(MyWin.height - point[1] * MyWin.height)             # range vertical coordinate to pyglet window

        if testing_with_eyetracker: 
            controller.recordEvent("calibration point\t{0}\t{1}\t\t{2}\t{3}".format(point[0],point[1],p_scaled[0],p_scaled[1]))     # write event to eyetracker data file
                   
        while not MyWin.has_exit:                                           # show point

            glClearColor(fg_color[0],fg_color[1],fg_color[2],1)             # set background color
            MyWin.clear()                                                   # clear window
            MyWin.dispatch_events()                                         # dispatch window events (very important call)

            ######################################################
            ## CHECK INPUT
            ######################################################
            lastevent = my_dispatch_events(MyWin, lastevent)                # my_dispatch_events is defined in rlabs_libutils
            if lastevent.type != []:                                        # check if last event is SPACE BAR or ...
                if lastevent.id == 32 and lastevent.type == "Key_UP":       # if it is space
                    lastevent.reset_values()                                # reset values of event
                    break

            ######################################################  
            ## Draw point
            ######################################################
            drawCircle(p_scaled[0], p_scaled[1], radius = 10, circle_color = (0,0,0))
            drawCircle(p_scaled[0], p_scaled[1], radius = 3, circle_color = (1,1,1))

            ######################################################  
            ## Flip the window
            ######################################################
            MyWin.flip()                                                    # flip window

            pass
        
        if MyWin.has_exit:                                                   # This breaks the For stimulus loop. 
            break                                                           

    pass

def drawline(a, b, color = (1.0,1.0,1.0)):
    # a and b are [x,y] arrays
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    glColor3f( color[0] , color[1], color[2])
    glBegin(GL_LINES)
    glVertex2f(a[0], a[1])
    glVertex2f(b[0], b[1])
    glEnd()

# if __name__ == "__main__":
#     eb = EyetrackerBrowser()
#     eb.main()

