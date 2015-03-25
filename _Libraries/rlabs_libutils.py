import math                         # for the circle
from pyglet.gl import *             # for the circle
import time                         # for the update method of the gratings
import csv                          # for reading the forced transition file
import os, stat                     # to create read-only file
import numpy as np                  # for camera sin and cos
from pyglet.window import key,mouse # for event handler

# misc functions -------------------------------------------------------------------------------------------------
def perm(x,n):
    """
    Combine each element of the array x
    in tuples of length n
    (with repetition).
    """
    from itertools import product       # cartesian product
    combination = []                    # initialize array
    for p in product(x, repeat = n):    # for each combination
        combination.append(p)           # append to list
    return combination                  # retun complete list

def merge_dicts(*dict_args):
    '''
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    '''
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

def merge_dicts_ordered(*dict_args):
    '''
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    '''
    from collections import OrderedDict
    result = OrderedDict()
    for dictionary in dict_args:
        result.update(dictionary)
    return result

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
    
    if val < value:     # if there's no value above
        val = -1        # use -1 for val
        idx = 0         # and 0 for idx


    return val, idx

# Data management functions and classes --------------------------------------------------------------------------

class EventItem():
    def __init__(self, name = '', counter = '', timestamp = '', etype = '', eid = '', ETtime = '', code = ''):
        self.name       = name
        self.counter    = counter
        self.timestamp  = timestamp
        self.type       = etype
        self.id         = eid
        self.ETtime     = ETtime # time of the eyetracker
        self.code       = code
        
class DataStruct(object):
    
    def __init__(self):

        self.eventsCounter       = [0]
        self.event_counter_array = []
        self.time_array          = []
        self.event_type_array    = []
        self.ID_array            = []
        self.trial_index_array   = []

class LastEvent():
    def __init__(self):
        self.type    = []
        self.id      = []
        self.counter = []

    def reset_values(self):
        self.type    = []
        self.id      = []
        self.counter = []

def save_data_to_arrays(lastevent, data_struct, trial, timeNow):
    """
    Appends each new event of an instance of the class 
    LastEvent() to the correspondent array of an instance 
    of the the class LastEvent()
    
    arguments
        - lastevent:    instance of LastEvent class
        - data_struct:  instance of DataStruct class
        - trial:        number of the current trial
        - timeNow:      call to time.time() 
        
    returns
        Nothing -- data_struct will be updated

    """
    # add event data to arrays
    data_struct.eventsCounter[0] += 1
    data_struct.event_counter_array.append(data_struct.eventsCounter[0])
    data_struct.time_array.append(timeNow)
    data_struct.event_type_array.append(lastevent.type) 
    data_struct.ID_array.append(lastevent.id)
    data_struct.trial_index_array.append(trial)        

def save_raw_data(rawdata_filename, data_struct):
    # """
    # Save contents of data_struct to output file
    # arguments
    #   - rawdata_filename: name of output file
    #   - data_struct:      instance of DataStruct class
        
    # returns
    #   Nothing --
    #"""
    timeStampStart = 0#data_struct.time_array[0]



    length = len(data_struct.event_counter_array)
    with open(rawdata_filename, 'w' ) as txtfile:
        for i in range(length):
            txtfile.write(str(data_struct.event_counter_array[i]) +'\t'+ str(data_struct.trial_index_array[i]) +'\t'+ str((data_struct.time_array[i]-timeStampStart)) +'\t'+ str(data_struct.event_type_array[i]) +'\t'+str(data_struct.ID_array[i])+'\n')
    # print("raw data saved")

    os.chmod(rawdata_filename,stat.S_IREAD) # make file read only

    pass

def save_data_formatted(data_namefile, data_struct, right_keys, left_keys):
    # """
    # Save contents of data_struct to output file in HARDCODED format.
    
    # Format is:
    # 1     - right key down (pressed)
    # 2 - right key up (released)
    # -1    - left  key down (pressed)
    # -2    - left key up (released)
    
    # arguments
    #   - rawdata_filename:     name of output file
    #   - data_struct:          instance of DataStruct class
    #   - right_keys:           array with ascii codes for right keys
    #   - left_keys:            array with ascii codes for left keys
    # returns
    #   Nothing --
    # """

    timeStampStart = 0#data_struct.time_array[0]

    length = len(data_struct.event_counter_array)
    with open(data_namefile, 'w' ) as txtfile:
        
        for i in xrange(0,length,1): # equal to for(i = 1, i <length, < i++)
            
            # this will look at the last two characters of the current event_type_array and will determine if it is up or down
            isdown  = (data_struct.event_type_array[i][len(data_struct.event_type_array[i])-2:len(data_struct.event_type_array[i])] == "DW")
            isup    = (data_struct.event_type_array[i][len(data_struct.event_type_array[i])-2:len(data_struct.event_type_array[i])] == "UP")
            
            
            if   (data_struct.ID_array[i] in right_keys) and (isdown):
                code = 1
                pass
            
            elif (data_struct.ID_array[i] in right_keys) and (isup):
                code = 2
            
            elif (data_struct.ID_array[i] in left_keys) and (isdown):
                code = -1
                pass
            
            elif (data_struct.ID_array[i] in left_keys) and (isup):
                code = -2
            
            else: # key not in right and left arrays
                code = 999 
            

            # data file
            # ToDo: put a column for number of trials too
            txtfile.write(str(data_struct.event_counter_array[i]) +'\t'+ str(data_struct.trial_index_array[i]) +'\t'+ str((data_struct.time_array[i]-timeStampStart)) +'\t'+ str(code) +'\n')
 
    os.chmod(data_namefile,stat.S_IREAD) # make file read only
    # print("formatted data saved")
 
    pass

def write_data_file(data_namefile, data_struct, right_keys = [4], left_keys = [1]):

    # fields in header:
    fields = ['Timestamp', 'EventName', 'EventType', 'EventID', 'EventCode', 'EventCount']

    timeStampStart = data_struct[0].timestamp
   
    with open(data_namefile, 'w' ) as f:            # open or create text file 'filename' to write
        f.write('\t'.join(fields)+'\n')             # write header. Separate the fields into tabs

        for e in data_struct:

            # compute code
            if e.name == 'InputEvent':

                isdown  = 'DW' in e.type
                isup    = 'UP' in e.type
                               
                if   (e.id in right_keys) and (isdown):
                    code = 4
                    pass
                
                elif (e.id in right_keys) and (isup):
                    code = -4
                
                elif (e.id in left_keys) and (isdown):
                    code = 1
                    pass
                
                elif (e.id in left_keys) and (isup):
                    code = -1
                
                else: # key not in right and left arrays
                    code = 999 

            elif e.name == 'TrialEvent':
                code = 8 if e.id == 'START' else -8


            f.write('{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n'.format(e.timestamp - timeStampStart, e.name, e.type, e.id, code, e.counter))
        
    os.chmod(data_namefile,stat.S_IREAD)                # make file read only


    pass

def write_data_file_with_parameters(data_namefile, data_struct, parameters, right_keys = [4], left_keys = [1]):
    """ write data file including events (mouse, trials) and configuration and trials parameters"""
    from itertools import izip_longest                                  # import itertools to iterate over two variables

    ntrials = parameters['number of trials']                            # get number of trials
    timeStampStart = data_struct[0].timestamp                           # get time stamp of the start of trial 1

    fields = ['Timestamp', 'EventName', 'EventType', 'EventID',         # create header
    'EventCode', 'EventCount', 'Parameters']

    for n in range(ntrials):                                            # for each trial
        fields.append('Value for trial {0}'.format(n+1))                # add field in header 
   
    with open(data_namefile, 'w' ) as f:                                # open or create text file 'data_namefile' to write
        f.write('\t'.join(fields)+'\n')                                 # write header. Separate the fields with tabs

        for e, b in izip_longest(data_struct, parameters.items()):      # iterate over data_struct and parameters until longest is over
        
            if e is not None:                                           # if event in data_struct is not None
                e = compute_event_code(e)                               # compute code for each one
                f.write('{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t'.format(        # and write it in data file
                    e.timestamp - timeStampStart, e.name,               
                    e.type, e.id, e.code, e.counter))
            else:                                                       # if event is None (because there are more parameters)
                f.write('-\t-\t-\t-\t-\t-\t')                           # fill rows with '-'

            if b is not None:                                           # if b (each pair of (key, value) in parameters dict) is not None
                k, v = b[0], b[1]                                       # get k and v (key and value)
           
                f.write('{0}'.format(k))                                # write key (name of parameter)
                if type(v) in (int, float, str) or 'color' in k:        # If it is a config parameter,
                    for i in range(ntrials):                            # write it (value will repeat
                        f.write('\t{0}'.format(v))                      # for each trial column).
                else:                                                   # If it is a trial parameter
                    for i in range(ntrials):                            # write the value
                        f.write('\t{0}'.format(v[i]))                   # for each trial.
            else:                                                       # if there are more events than parameters
                f.write('-\t'*(ntrials+1))                              # fill columns with '-'

            f.write('\n')                                               # new line
        
    os.chmod(data_namefile,stat.S_IREAD)                                # make file read only

def compute_event_code(e, codes = [1, 4, 8, 999], downcode = 'DW', upcode = 'UP', right_keys  = [4, 109, 110, 106], left_keys   = [1, 122, 120, 115]):
    """
    Compute code that will be later used in data analysis.
    
    Legend:
    event:                code
    LEFT  mouse press:    1
    LEFT  mouse release: -1
    RIGHT mouse press:    4
    RIGHT mouse release: -4
    Trial start:          8
    Trial end:           -8

    event not expected:  999
    """

    if e.name == 'InputEvent':

        isdown  = downcode  in e.type           
        isup    = upcode    in e.type           
                       
        if   (e.id in right_keys) and (isdown): 
            e.code = codes[1]                   
        
        elif (e.id in right_keys) and (isup):
            e.code = -codes[1]
        
        elif (e.id in left_keys) and (isdown):
            e.code = codes[0]
        
        elif (e.id in left_keys) and (isup):
            e.code = -codes[0]
        
        else: # key not in right and left arrays
            e.code = codes[3]

    elif e.name == 'TrialEvent':
        e.code = 8 if 'START' in e.id else -8

    return e


def create_unique_name(subject_info):
    
    ## Create output data file name
    
    # Get subject and time information
    exp_name = 'pythonMigration'
    time_string = time.strftime("%y.%m.%d_%H.%M.%S", time.localtime())
    subject_name = subject_info["Name"]
    
    textfilename = (exp_name + '_' + subject_name + '_' + time_string + '.txt')
    
    # Save output file in the folder "data".
    # following command will create the native file separator caracter. e.g.: '\' for windows
    out_file_name = os.path.join('data', textfilename) 

    return out_file_name    

# -------------------------------------------------------------------------------------------------------------------

class MyWindow(pyglet.window.Window): 
    """
        MyWindow is a subclassed pyglet window class.
        Used to add to the window a variable called 'events'
        that will contain the mouse and keyboard events that 
        occurred in the window.
    """
    
    def __init__(self, config = None, fullscreen = False, screen = None, visible = 1):
        super(MyWindow, self).__init__(config = config, fullscreen = fullscreen, screen = screen, visible = visible) 

        self.events = []
        self.events_handler = None

    def on_mouse_press(self, x, y, button, modifiers):
        e = EventItem(name = 'InputEvent', timestamp = time.time(), etype = 'Mouse_DW', eid = button)
        self.events.append(e)
        
        if self.events_handler:
            # handler = self.events_handler.get((button,'PRESS'), lambda: None)(x,y)
            handler = self.events_handler.get('on_mouse_press', lambda: None)(e)
            # handler()

    def on_mouse_release(self, x, y, button, modifiers):
        e = EventItem(name = 'InputEvent', timestamp = time.time(), etype = 'Mouse_UP', eid = button)
        self.events.append(e)
        
        if self.events_handler:
            # handler = self.events_handler.get((button,'RELEASE'), lambda: None)(x,y)
            handler = self.events_handler.get('on_mouse_release', lambda: None)(e)
            # handler()

    def on_key_press(self, symbol, modifiers):
        e = EventItem(name = 'InputEvent', timestamp = time.time(), etype = 'Key_DW', eid = symbol)
        self.events.append(e)

        if symbol == pyglet.window.key.ESCAPE:
            super(MyWindow, self).on_close()

        if self.events_handler:
            handler = self.events_handler.get((symbol,'PRESS'), lambda: None)
            handler()

    def on_key_release(self, symbol, modifiers):
        e = EventItem(name = 'InputEvent', timestamp = time.time(), etype = 'Key_UP', eid = symbol)
        self.events.append(e)

        if self.events_handler:
            handler = self.events_handler.get((symbol,'RELEASE'), lambda: None)
            handler()

    def reset_events(self):
        self.events = []

    def on_draw(self): 
        self.clear()

    def get_last_event(self):
        if self.events != []:
            return self.events[-1]
        else:
            # return EventItem(name = '-', timestamp = time.time(), etype = '-', eid = '-')
            return

def my_dispatch_events(mywindow, event):
    """
    Appends each new event of an instance of the class 
    LastEvent() to the correspondent array of an instance 
    of the the class LastEvent()
    
    arguments
        - mywindow: instance of a pyglet Window class
        - event: instance of LastEvent class
        
    returns
        - event: event will be updated

    """
    @mywindow.event
    def on_key_press(symbol, modifiers): 
        event.type       = "Key_DW"
        event.id         = symbol
        # event.counter    += 1

    @mywindow.event
    def on_key_release(symbol, modifiers):
        event.type       = "Key_UP"
        event.id         = symbol
        # event.counter    += 1

    @mywindow.event
    def on_mouse_press(x, y, button, modifiers):
        event.type       = "Mouse_DW"
        event.id         = button
        # event.counter    += 1

    @mywindow.event
    def on_mouse_release(x, y, button, modifiers):
        event.type       = "Mouse_UP"
        event.id         = button
        # event.counter    += 1

    
    @mywindow.event
    def on_close():
        # The closing of the window is taken care in the while loop
        pass
    return event

def wait_for_go_function(mywindow, event, expected_type = 'Mouse_UP', expected_id = 2):
    
    wait_for_go = 0
    
    mywindow.dispatch_events()
    event = my_dispatch_events(mywindow,event)

    # Calculate condition for "go", for example:
    #  -the mouse was clicked (any key), OR
    #  -SPACE key was pressed (ASCII 32 key)
    # if (event.type == "Key_DW" and event.id == 32) or (event.type=="Mouse_UP"):
        # wait_for_go = 1

    # Calculate condition for "go", for example:
    # Default: when mouse-wheel is released
    if (event.type == expected_type and event.id == expected_id):
        wait_for_go = 1

    event.reset_values()
            
    return wait_for_go
    pass    

def my_on_close(mywindow):
    # Save data +do whatever other pre-exit cleanup necessary
    print("closed nicely")   
    mywindow.clear()
    mywindow.close()

# events_handler example. It needs to be in the main function because 'events_struct' is used ----------------------
events_handler = {
    'on_mouse_press'    : lambda e: events_struct.append(e),
    'on_mouse_release'  : lambda e: events_struct.append(e),
}


events_handler_with_ET = {                      # if using eyetracker, use this
    'on_mouse_press'    : lambda e: (events_struct.append(e), controller.myRecordEvent2(event = e)),
    'on_mouse_release'  : lambda e: (events_struct.append(e), controller.myRecordEvent2(event = e)),
}

# Stimulus functions and classes -----------------------------------------------------------------------------------
def draw_cross(x, y, length1 = 100, length2 = 100, color = (255,255,255), line_width = 1):
    center = x, y
    vertices = center[0] - length1/2, center[1], center[0] + length1/2, \
        center[1], center[0], center[1] + length2/2, center[0], center[1] - length2/2       # compute vertices given the center
    n = len(vertices)/2                                                                     # number of points
    pyglet.gl.glLineWidth(line_width)                                                       # set lines width
    pyglet.graphics.draw(n, pyglet.gl.GL_LINES,                                             # draw lines
        ('v2f', vertices),
        ('c3B', color * n),
        )

def drawpoints(vertices, color = (255,255,255), size = 1):
    n = len(vertices)/2                                     # number of points
    glEnable(GL_POINT_SMOOTH)                               # enable smoothing, if not, points will be squares
    pyglet.gl.glPointSize(size)                             # resize points
    pyglet.graphics.draw(n, pyglet.gl.GL_POINTS,            # draw points
        ('v2f', vertices),
        ('c3B', color * n),
        )

def drawCircle(x, y, numTheta = 90, radius = 100, circle_color = (0,0,0)):

    deltaTheta = 2 * math.pi / numTheta

    glColor3f( circle_color[0] , circle_color[1], circle_color[2])
      
    for i in range (0, numTheta):
        cx1 = x + radius * math.sin(deltaTheta * i)
        cy1 = y + radius * math.cos(deltaTheta * i)
        cx2 = x + radius * math.sin(deltaTheta * (i+1))
        cy2 = y + radius * math.cos(deltaTheta * (i+1))
          
        glBegin( GL_TRIANGLES )
        glVertex2f(x, y )
        glVertex2f(cx1 , cy1 )
        glVertex2f(cx2 , cy2 )
        glEnd()

def drawGrating(x, y, fill_color, orientation, mylambda, duty_cycle, apertRad_pix):
     
    bar_length = 1000
 
    radio_aux = (2 * apertRad_pix) + mylambda #diameter 
    num_bars = int(1 + math.floor(radio_aux / mylambda))+3
   
    glStencilFunc (GL_EQUAL, 0x1, 0x1) 
    glStencilOp (GL_KEEP, GL_KEEP, GL_KEEP)
         
    glLoadIdentity() #replace current matrix with the identity matrix
    glTranslatef(x, y, 0)
    glRotatef(orientation,0,0,1)    
    glTranslatef(-x, -y, 0)
 
    glColor3f(fill_color[0] , fill_color[1], fill_color[2] )
     
    glBlendFunc(GL_ZERO, GL_SRC_COLOR)  
     
    for i in range(int(-num_bars/2),int(num_bars/2)):    
         
        x1 = mylambda * i + x
        x2 = (duty_cycle * mylambda) + (mylambda * i + x)
         
        glBegin(GL_QUADS)
         
        glVertex2f(x1, y - bar_length) 
        glVertex2f(x1, y + bar_length) 
        glVertex2f(x2, y + bar_length) 
        glVertex2f(x2, y - bar_length)
         
        glEnd()
     
    # glRotatef(-orientation, 0, 0, 1)#Is it necessary?
    glBlendFunc(GL_ONE, GL_ZERO)
    glLoadIdentity()
    pass

def drawAperture(x0_pix, y0_pix, radius_pix, color, numTheta):

    # Enable stencil
    glClearStencil(0x0)
    glEnable(GL_STENCIL_TEST) 
        
    #define the region where the stencil is 1
    glClear(GL_STENCIL_BUFFER_BIT)
    glStencilFunc(GL_ALWAYS, 0x1, 0x1) #Always pass stencil functions test
    glStencilOp(GL_REPLACE, GL_REPLACE, GL_REPLACE) #Replace stencil value with reference value
    
    drawCircle(x0_pix, y0_pix, numTheta, radius_pix, color)
    pass

class Grating():
    def __init__(self, MyWin, x, y, fill_color, orientation, mylambda, duty_cycle, apertRad_pix, speed):
        self.x            = x
        self.y            = y
        self.fill_color   = fill_color
        self.orientation  = orientation
        self.mylambda     = mylambda
        self.duty_cycle   = duty_cycle
        self.apertRad_pix = apertRad_pix
        self.speed        = speed

        # decide if horizontal or vertical motion, depending on orientation:
        # self.threshold_angle = 50
        # if orientation < self.threshold_angle:
        #     self.motion_cycle = mylambda/(math.cos(math.radians(orientation)))
        #     self.initialpos = x
        # elif orientation >= self.threshold_angle:
        #     self.motion_cycle = mylambda/(math.sin(math.radians(orientation)))
        #     self.initialpos = y
        #     # self.initialpos = MyWin.width/2 - apertRad_pix - mylambda/2
        self.motion_cycle = mylambda/(math.cos(math.radians(orientation)))
        self.initialpos = x
 
        pass
     
    def draw(self):
        x            = self.x
        y            = self.y
        fill_color   = self.fill_color
        orientation  = self.orientation
        mylambda     = self.mylambda
        duty_cycle   = self.duty_cycle
        apertRad_pix = self.apertRad_pix
         
         
        bar_length = 1000
     
        radio_aux = (2 * apertRad_pix) + mylambda #diameter 
        num_bars = int(1 + math.floor(radio_aux / mylambda))+3
       
        glStencilFunc (GL_EQUAL, 0x1, 0x1) 
        glStencilOp (GL_KEEP, GL_KEEP, GL_KEEP)
             
        glLoadIdentity() #replace current matrix with the identity matrix
        glTranslatef(x, y, 0)
        glRotatef(orientation,0,0,1)    
        glTranslatef(-x, -y, 0)
     
        glColor3f(fill_color[0] , fill_color[1], fill_color[2] )
         
        glBlendFunc(GL_ZERO, GL_SRC_COLOR)  
         
        for i in range(int(-num_bars/2),int(num_bars/2)):    
             
            x1 = mylambda * i + x
            x2 = (duty_cycle * mylambda) + (mylambda * i + x)
             
            glBegin(GL_QUADS)
             
            glVertex2f(x1, y - bar_length) 
            glVertex2f(x1, y + bar_length) 
            glVertex2f(x2, y + bar_length) 
            glVertex2f(x2, y - bar_length)
             
            glEnd()
         
        # glRotatef(-orientation, 0, 0, 1)#Is it necessary?
        #glBlendFunc(GL_ONE, GL_ZERO) #150116 comment out NR
        glLoadIdentity()
        pass
     
    def update_position(self, runningTime, stereo):
        motion_cycle = self.motion_cycle
        speed        = self.speed
        initialpos   = self.initialpos
         
        timeNow = time.time()

        position = initialpos + stereo

        self.x = position + math.fmod(speed*(timeNow-runningTime), motion_cycle)
        # if self.orientation < self.threshold_angle:
        #     self.x = position + math.fmod(speed*(timeNow-runningTime), motion_cycle)
        # elif self.orientation >= self.threshold_angle:
        #     self.y = initialpos + math.fmod(speed*(timeNow-runningTime), motion_cycle)

        pass
     
    pass    

class mycoords():
    # OpenGL coordinate system (0,0) is at the bottom left of the screen
    # this funciton makes the cordinate system at the center of the scree
    def __init__(self,x,y,window):
        self.x = x + window.width/2
        self.y = y + window.height/2


# Forced mode functions --------------------------------------------------------------------------------------------

def read_forced_transitions(transfilename='datatestN_NR_5_trans.txt'):
    transfilename = 'datatestN_NR_5_trans.txt'
    #forced = 1
    deltaXaux1_ini = 0
    deltaXaux2_ini = 0
    deltaX1 = 0.01
    deltaX2 = 0.01
    # transfilename = 'datatestN_NR_5_trans.txt'
    # transfilename_full = os.path.join(application_path, transfilename)    # Full path name of the transition file
    # 5.1 - Read file with transition time stamps (for forced mode)
    transTimeL = []
    transTimeR = []
    
    try:                                                            # try/except is used here to handle errors such 
        with open(transfilename, 'r') as f:                 # as the transition file name is wrong
        #with open(transfilename) as f:
        #with open('trans.txt') as f: 
            reader=csv.reader(f,delimiter='\t')                     # reader is a csv class to parse data files
        
            for L_item,R_item in reader:                            #L_item and R_item are the time stamps
            #for R_item,L_item in reader:                            #L_item and R_item are the time stamps
                #L_array.append(float(L_item))                              # Append time stamps to array
                #R_array.append(float(R_item))
                transTimeL.append(float(L_item))                              # Append time stamps to array
                transTimeR.append(float(R_item))
        
        #L_array.append(timeTrialMax)                                # Append total duration of trial at the end?
        #R_array.append(timeTrialMax)
                
        #timeTransL = L_array[0]        
        #timeTransR = R_array[0]
        # timeRamp = 0.5
        
        
        
    except EnvironmentError:
        #print srt(transfilename)+' could not be opened'
        print "transition file could not be opened"
        sys.exit()
    
    return transTimeL,transTimeR       

def compute_forced_values(i_R, i_L, Ron, Lon, timeTransR, timeTransL, deltaXaux1, deltaXaux2, timeRamp, timeStartTrial,timeNow, transTimeL, transTimeR, deltaX1=0.01, deltaX2=0.01, deltaXaux1_ini=0, deltaXaux2_ini=0):
    # Apply forced mode changes to the stereo
    # Moving the Depth
    scale = 500

    if (timeNow - timeStartTrial > timeTransR) & (timeNow - timeStartTrial < timeTransR + timeRamp):
        
        deltaXaux1 = deltaX1 * (timeNow - timeStartTrial - timeTransR) / timeRamp
        Ron = 1
        
        if deltaXaux2_ini > deltaX2/2:
            deltaXaux2 = deltaX2 - deltaX2 * (timeNow - timeStartTrial - timeTransR) / timeRamp
        
        deltaXaux1_ini = deltaXaux1
        
    if (timeNow - timeStartTrial > timeTransR + timeRamp) & (Ron == 1):
        Ron = 0
        i_R = i_R + 1
        timeTransR = transTimeR[i_R]
    # print timeTransR
        
    if (timeNow - timeStartTrial > timeTransL) & (timeNow - timeStartTrial < timeTransL + timeRamp):
        
        deltaXaux2 = deltaX2 * (timeNow - timeStartTrial - timeTransL) / timeRamp
        Lon = 1
        
        if (deltaXaux1_ini > deltaX1/2):
            deltaXaux1 = deltaX1 - deltaX1 * (timeNow - timeStartTrial - timeTransL) / timeRamp
        
        deltaXaux2_ini = deltaXaux2
    
    if (timeNow - timeStartTrial > timeTransL + timeRamp) & (Lon == 1):
        Lon = 0
        i_L = i_L + 1
        timeTransL = transTimeL[i_L]
    
    # update stereo value
    stereo1 = (-deltaXaux1/2 + deltaXaux2/2) * scale
    stereo2 =  (deltaXaux1/2 - deltaXaux2/2) * scale

    return stereo1, stereo2, i_R, i_L, Ron, Lon, timeTransR, timeTransL, deltaXaux1, deltaXaux2


# Camera (from http://tartley.com/?p=378) ---------------------------------------------------------------------------

"""
Camera tracks a position, orientation and zoom level, and applies openGL
transforms so that subsequent renders are drawn at the correct place, size
and orientation on screen
"""

class Target(object):

    def __init__(self, camera):
        self.x, self.y = camera.x, camera.y
        self.scale = camera.scale
        self.angle = camera.angle


class Camera(object):

    def __init__(self, position=None, scale=None, angle=None):
        if position is None:
            position = (0, 0)
        self.x, self.y = position
        if scale is None:
            scale = 1
        self.scale = scale
        if angle is None:
            angle = 0
        self.angle = angle
        self.target = Target(self)




    def zoom(self, factor):
        self.target.scale *= factor
        # print self.scale

    def pan(self, length, angle):
        self.target.x += length * np.sin(angle + self.angle)
        self.target.y += length * np.cos(angle + self.angle)


    def tilt(self, angle):
        self.target.angle += angle


    def update(self):
        self.x += (self.target.x - self.x) * 0.1
        self.y += (self.target.y - self.y) * 0.1
        self.scale += (self.target.scale - self.scale) * 0.1
        self.angle += (self.target.angle - self.angle) * 0.1


    def focus(self, width, height):
        "Set projection and modelview matrices ready for rendering"

        # Set projection matrix suitable for 2D rendering"
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = width / height
        # print self.scale * aspect
        gluOrtho2D(                 # define a 2D orthographic projection matrix
            -self.scale * aspect,   # gluOrtho2D sets up a two-dimensional orthographic viewing region
            +self.scale * aspect,
            -self.scale,
            +self.scale)

        # Set modelview matrix to move, scale & rotate to camera position"
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            self.x, self.y, +1.0,
            self.x, self.y, -1.0,
            np.sin(self.angle), np.cos(self.angle), 0.0)


    def hud_mode(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, width, 0, height)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()





# Not used -----------------------------------------------------------------------------------

class Aperture():
    def __init__(self, color, numTheta, x0_pix, y0_pix, radius_pix):
        self.color      = color
        self.numTheta   = numTheta
        self.x0         = x0_pix
        self.y0         = y0_pix
        self.radius     = radius_pix
        pass
    
    def draw(self):
        color           = self.color
        numTheta        = self.numTheta
        x0_pix          = self.x0
        y0_pix          = self.y0
        apertRad_pix    = self.radius
        
        
        # Enable stencil
        glClearStencil(0x0)
        glEnable(GL_STENCIL_TEST) 
            
        #define the region where the stencil is 1
        glClear(GL_STENCIL_BUFFER_BIT)
        glStencilFunc(GL_ALWAYS, 0x1, 0x1) #Always pass stencil functions test
        glStencilOp(GL_REPLACE, GL_REPLACE, GL_REPLACE) #Replace stencil value with reference value
        
        drawCircle(x0_pix, y0_pix, numTheta, apertRad_pix, color)
        pass
    
    pass



