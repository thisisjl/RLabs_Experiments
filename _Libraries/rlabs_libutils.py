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
    out = {}
    for dictionary in dict_args:
        out.update(dictionary)
    return out

def merge_dicts_ordered(*dict_args):
    '''
    Given any number of dicts, shallow copy and merge into a new OrderedDict,
    precedence goes to key value pairs in latter dicts.
    '''
    from collections import OrderedDict
    out = OrderedDict()
    for dictionary in dict_args:
        out.update(dictionary)
    return out

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
        
class _DataStruct(object):
    
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

class FakeSecHead(object):
    """ 
    To read config files without sections 
    using ConfigParser python module 
    from: http://stackoverflow.com/questions/2819696/parsing-properties-file-in-python/2819788#2819788
    """

    def __init__(self, fp):
        self.fp = fp
        self.sechead = '[asection]\n'

    def readline(self):
        if self.sechead:
            try: 
                return self.sechead
            finally: 
                self.sechead = None
        else: 
            return self.fp.readline()

class DataStruct():
    def __init__(self, datafile, A_code = 1, B_code = 4, trial_code = 8, epsilon = 0.0123, plotrange = [-1.1,1.1], 
        winwidth_pix = 1280, winwidth_cm = 35.6, fixdist = 60.0, dataframerate = 120.0):
        
        self.filenamefp     = datafile      # full path of data file
        self.filename       = ''            # data filename 
        self.eyetrackerdata = False         # True if et data, False if just input
        self.numtrials      = 0             # number of trials in data file

        # eyetracker data
        self.timestamps     = []            # eyetracker time stamps
        self.leftgazeX      = []            # 
        self.leftgazeY      = []            # 
        self.rightgazeX     = []            # 
        self.rightgazeY     = []            # 
        self.leftvalidity   = []            #
        self.rightvalidity  = []            #

        self.leftgazeXvelocity  = []        # to allocate velocity
        self.rightgazeXvelocity = []        # which will be computed
        self.leftgazeYvelocity  = []        # in self.read_data()
        self.rightgazeYvelocity = []        #


        self.trial_ts   = []                # time stamps for trials

        # percept data
        self.A_trial    = []                # time stamps for A in trial
        self.B_trial    = []                # time stamps for B in trial
        self.A_ts       = []                # time stamps for A
        self.B_ts       = []                # time stamps for B

        # constants
        self.A_code     = A_code            # code value for A percept
        self.B_code     = B_code            # code value for B percept
        self.trial_code = trial_code        # code value for trials
        self.epsilon    = epsilon           # epsilon
        self.plotrange  = plotrange         # plotrange 

        self.winwidth_pix = winwidth_pix    #
        self.winwidth_cm  = winwidth_cm     #
        self.fixdist      = fixdist         #
        self.framerate    = dataframerate   #
        
        

        self.read_data()                    # read data

        self.expname = ''
        self.subjectname = ''

    def read_data(self):
        # Read data file --------------------------------------------------------------------------------------------
        self.filename = os.path.split(self.filenamefp)[1]                                       # get just data file name, not full path
        try:
            data = np.genfromtxt(self.filenamefp, delimiter="\t",                               # read data file, dtype allows mixed types of data,
            dtype=None, names=True, usecols = range(38))                                        # names reads first row as header, usecols will read just 38 columns
        except ValueError:
            try: 
                data = np.genfromtxt(self.filenamefp, delimiter="\t", 
                    dtype=None, names=True, usecols = range(34))                                        
            except ValueError:
                try:
                    data = np.genfromtxt(self.filenamefp, delimiter="\t", 
                    dtype=None, names=True, usecols = range(9))
                except ValueError:
                    print 'cannot read data file'
                    sys.exit()

        # Determine if datafile contains eyetracker data or just input (mouse) ----------------------------------------
        et_data = True if 'LeftGazePoint2Dx' in data.dtype.names else False                     # if LeftGazePoint2Dx in header, et_data is True, else is False

        
        # Read events data --------------------------------------------------------------------------------------------
        if et_data:
            try:
                ets       = data['EventTimeStamp'][data['EventTimeStamp']!='-'].astype(np.float)        # event time stamp: filter out values with '-' and convert str to float
                ecode     = data['Code'][data['Code'] != '-'].astype(np.float)                          # event code: filter out values with '-' and convert to float
            except ValueError:
                print data.dtype.names
        else:
            ets       = data['EventTimeStamp']                                                      # event time stamp: filter out values with '-' and convert str to float
            ecode     = data['Code']                                                                # event code: filter out values with '-' and convert to float
        # print data['Code']

        Trial_on  = ets[ecode ==  self.trial_code]                                              # get timestamp of trials start
        Trial_off = ets[ecode == -self.trial_code]                                              # get timestamp of trials end

        A_on      = ets[ecode ==  self.A_code]                                                  # get timestamp of percept A on (LEFT press)
        A_off     = ets[ecode == -self.A_code]                                                  # get timestamp of percept A off (LEFT release)

        B_on      = ets[ecode ==  self.B_code]                                                  # get timestamp of percept B on (RIGHT press)
        B_off     = ets[ecode == -self.B_code]                                                  # get timestamp of percept B off (RIGHT release)

        self.numtrials = len(Trial_on)                                                          # compute number of trials

        # datastruct
        self.trial_ts = np.empty((Trial_on.size + Trial_off.size,), dtype=Trial_on.dtype)       # create empty matrix of specific lenght
        self.trial_ts[0::2] = Trial_on                                                          # put Trial_on on even spaces 
        self.trial_ts[1::2] = Trial_off                                                         # put Trial_off on odd spaces

        # Check input events --------------------------------------------------------------------------------------------

        # Get input in each trial
        x, y, z = 2, 0, self.numtrials                                                          # size of percept matrix
        self.A_trial = [[[0 for k in xrange(x)] for j in xrange(y)] for i in xrange(z)]         # matrix for A percept of each trial
        self.B_trial = [[[0 for k in xrange(x)] for j in xrange(y)] for i in xrange(z)]         # matrix for B percept of each trial

        for trial in range(self.numtrials):                                                     # for each trial
            start = self.trial_ts[2 * trial]                                                    # timestamp start of trial
            end   = self.trial_ts[2 * trial + 1]                                                # timestamp end of trial

            A_on_in_trial = [i for i in A_on if start<i<end]                                    # get A_on in trial

            for ts_on in A_on_in_trial:                                                         # for each A_on
                val, idx_start = find_nearest_above(A_off, ts_on)                               # look for the nearest above A_off
                
                if val is not None:                                                             # compare nearest above to end of trial,
                    ts_off = np.minimum(end,val)                                                # get minimum                                               
                else:
                    ts_off = end

                self.A_trial[trial].append([ts_on, ts_off])                                     # add A_on and A_off times to percept matrix

            B_on_in_trial = [i for i in B_on if start<i<end]                                    # get A_on in trial

            for ts_on in B_on_in_trial:                                                         # for each B_on
                val, idx_start = find_nearest_above(B_off, ts_on)                               # look for the nearest above B_off
                
                if val is not None:                                                             # compare nearest above to end of trial,
                    ts_off = np.minimum(end,val)                                                # get minimum
                else:
                    ts_off = end

                self.B_trial[trial].append([ts_on, ts_off])                                     # add B_on and B_off times to percept matrix

            for item in self.A_trial[trial]:                                                    # datastruct.A/B_ts will contain on and off
                self.A_ts.append(item)                                                          # time staps in the following way:
            for item in self.B_trial[trial]:                                                    # [[on_1, off_2], [on_2, off_2] ...]
                self.B_ts.append(item)                                                          # 

        # Read eyetracker data ---------------------------------------------------------------------------------------
        if et_data:
            self.eyetrackerdata = True                                                          # indicate that datastruct contains eyetracker data

            self.timestamps     = np.array(map(float, data['Timestamp']))                       # get time stamps of the eye tracker data

            self.leftgazeX      = np.array(map(float, data['LeftGazePoint2Dx']))                # get left gaze X data
            self.leftgazeY      = np.array(map(float, data['LeftGazePoint2Dy']))                # get left gaze Y data
            self.leftvalidity   = np.array(map(float, data['LeftValidity']))                    # get left gaze validity
            
            self.rightgazeX     = np.array(map(float, data['RightGazePoint2Dx']))               # get right gaze X data
            self.rightgazeY     = np.array(map(float, data['RightGazePoint2Dy']))               # get right gaze Y data
            self.rightvalidity  = np.array(map(float, data['RightValidity']))                   # get right gaze validity

            self.vergence       = np.array(map(float, data['Vergence']))                        # get vergence
            self.fixationdist   = np.array(map(float, data['FixationDist']))                    # get fixation distance

            # Tobii gives data from 0 to 1, we want it from -1 to 1:
            self.leftgazeX      = 2 * self.leftgazeX    - 1
            self.leftgazeY      = 2 * self.leftgazeY    - 1
            self.rightgazeX     = 2 * self.rightgazeX - 1
            self.rightgazeY     = 2 * self.rightgazeY - 1

            # Map values outside of range to the boundaries
            self.leftgazeX[self.plotrange[0]  > self.leftgazeX]  = self.plotrange[0]; self.leftgazeX[self.plotrange[1] < self.leftgazeX] = self.plotrange[1]
            self.leftgazeY[self.plotrange[0]  > self.leftgazeY]  = self.plotrange[0]; self.leftgazeY[self.plotrange[1] < self.leftgazeY] = self.plotrange[1]
            self.rightgazeX[self.plotrange[0] > self.rightgazeX] = self.plotrange[0]; self.rightgazeX[self.plotrange[1] < self.rightgazeX] = self.plotrange[1]
            self.rightgazeY[self.plotrange[0] > self.rightgazeY] = self.plotrange[0]; self.rightgazeY[self.plotrange[1] < self.rightgazeY] = self.plotrange[1]

            # Compute velocity
            # 1 - convert gaze values from arbitrary units to pixels
            leftgazeX_pix  = self.leftgazeX  * self.winwidth_pix                                #
            rightgazeX_pix = self.rightgazeX * self.winwidth_pix
            leftgazeY_pix  = self.leftgazeY  * self.winwidth_pix
            rightgazeY_pix = self.rightgazeY * self.winwidth_pix

            # 2 - convert gaze values from pixels to degrees
            V = 2 * np.arctan(self.winwidth_cm/2 * self.fixdist)                                # in radians
            deg_per_pix = V / self.winwidth_pix                                                 # in degrees

            leftgazeX_deg  = leftgazeX_pix  * deg_per_pix                                       #
            rightgazeX_deg = rightgazeX_pix * deg_per_pix                                       #
            leftgazeY_deg  = leftgazeY_pix  * deg_per_pix                                       #
            rightgazeY_deg = rightgazeY_pix * deg_per_pix                                       #

            # 3 - compute velocity
            self.leftgazeXvelocity  = np.diff(leftgazeX_deg,  n=1) * self.framerate;            #
            self.rightgazeXvelocity = np.diff(rightgazeX_deg, n=1) * self.framerate;            #
            self.leftgazeYvelocity  = np.diff(leftgazeY_deg,  n=1) * self.framerate;            #
            self.rightgazeYvelocity = np.diff(rightgazeY_deg, n=1) * self.framerate;            #


            # compute percentage of validity
            self.dataloss = []
            
            for trial in range(self.numtrials):                                                 # for each trial
                start = self.trial_ts[2 * trial]                                                # timestamp start of trial
                end   = self.trial_ts[2 * trial + 1]                                            # timestamp end of trial

                # get row index
                val, idx_start = find_nearest_above(self.timestamps, start)
                val, idx_end   = find_nearest_above(self.timestamps, end)
                if idx_end is None: idx_end = len(self.timestamps)-1

                nsamples = idx_end - idx_start

                lv_trial = 100 * (self.leftvalidity[idx_start:idx_end] == 4).sum()/float(nsamples)  # left eye:  % of lost data
                rv_trial = 100 * (self.rightvalidity[idx_start:idx_end] == 4).sum()/float(nsamples) # right eye: % of lost data

                self.dataloss.append([lv_trial, rv_trial])

                print 'For trial {0}, {1} % of data was lost'.format(trial+1, "%.1f" % lv_trial)    # (e.g. validity equal to 4)


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

def write_data_file_with_parameters(data_namefile, data_struct, parameters, right_keys = [4], left_keys = [1], codes = [1, 4, 8, 999]):
    """ write data file including events (mouse, trials) and configuration and trials parameters"""
    from itertools import izip_longest                                  # import itertools to iterate over two variables

    ntrials = int(parameters['numtrials'])                              # get number of trials
    timeStampStart = data_struct[0].timestamp                           # get time stamp of the start of trial 1

    fields = ['EventTimeStamp', 'EventName', 'EventType', 'EventID',    # create header
    'Code', 'EventCount', 'Parameters']

    for n in range(ntrials):                                            # for each trial
        fields.append('Value-trial-{0}'.format(n+1))                # add field in header 
   
    with open(data_namefile, 'w' ) as f:                                # open or create text file 'data_namefile' to write
        f.write('\t'.join(fields)+'\n')                                 # write header. Separate the fields with tabs

        for e, b in izip_longest(data_struct, parameters.items()):      # iterate over data_struct and parameters until longest is over
        
            if e is not None:                                           # if event in data_struct is not None
                e = compute_event_code(e, codes = codes)                # compute code for each one
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

        self.last_event = None
        self.prev_events_len = None

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
        if self.events != [] and not len(self.events) == self.prev_events_len:      # if events is not empty and there's not the same number of events since last reset,
            self.last_event = self.events[-1]                                       # get last event
            return self.last_event                                                  # return last event
        else:
            return
    
    def reset_last_event(self):             
        self.prev_events_len = len(self.events)     # get length of events array, to compare when getting last event again
        self.last_event = None                      # set last_event to None

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

def drawCircle(x, y, radius = 100, color = (1.0, 1.0, 1.0, 1.0)):
    '''draws a circle of radius r centered at (x, y)'''
    draw_ring(x, y, 0, radius, color)

def draw_ring(x, y, inner, outer, color=(1.0, 1.0, 1.0, 1.0)):
    '''
    draws a ring of inner radius "inner" and outer radius "outer" centered at (x, y).
    from http://py-fun.googlecode.com/svn-history/r10/trunk/toolbox/graphics2d.py
    '''
    glPushMatrix()
    glColor3f(*color)
    glTranslatef(x, y, 0)
    q = gluNewQuadric()
    # a circle is written as a number of triangular slices; we use
    # a maximum of 360 which looked smooth even for a circle as
    # large as 1500 px.
    # Smaller circles can be drawn with fewer slices - the rule we
    # use amount to approximately 1 slice per px on the circumference
    slices = int(min(360, 6*outer))
    gluDisk(q, inner, outer, slices, 1)
    glPopMatrix()

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

def drawAperture(x0_pix, y0_pix, radius_pix, color):

    # Enable stencil
    glClearStencil(0x0)
    glEnable(GL_STENCIL_TEST) 
        
    #define the region where the stencil is 1
    glClear(GL_STENCIL_BUFFER_BIT)
    glStencilFunc(GL_ALWAYS, 0x1, 0x1) #Always pass stencil functions test
    glStencilOp(GL_REPLACE, GL_REPLACE, GL_REPLACE) #Replace stencil value with reference value
    
    drawCircle(x0_pix, y0_pix, radius_pix, color)
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

def read_forced_transitions(transfilename='forcedtransitions.txt'):
    transTimeL = []                                             # initialize Left  timestamps array
    transTimeR = []                                             # initialize Right timestamps array   
    try:                                                        # try/except used to handle errors
        with open(transfilename, 'r') as f:                     # open transitions file
            reader = csv.reader(f, delimiter='\t')              # reader is a csv class to parse data files

            for L_item, R_item in reader:                       # L_item and R_item are the time stamps
                transTimeL.append(float(L_item))                # append left time stamp to array
                transTimeR.append(float(R_item))                # append left time stamp to array

    except EnvironmentError:                                    # except: if the file name is wrong
        print '{0} could not be opened'.format(transfilename)   # print error
        sys.exit()                                              # exit python
    
    return transTimeL, transTimeR                               # return timestamps

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

class Forced_struct():
    def __init__(self, transfilename = 'forcedtransitions.txt', timeRamp = 0.5, scale = 500):
        self.transfilename = transfilename                              # get transitions file name
        self.timeRamp = timeRamp                                        # get stereo speeed
        self.scale = scale
        self.transTimeL = []                                            # initialize Left  timestamps array
        self.transTimeR = []                                            # initialize Right timestamps array
        
        self.read_forced_transitions()                                  # read transition time stamps

        # initialize forced variables
        self.i_R = 0
        self.i_L = 0
        self.Ron = 0
        self.Lon = 0
        self.timeTransR = self.transTimeL[0]
        self.timeTransL = self.transTimeR[0]
        self.deltaXaux1 = 0
        self.deltaXaux2 = 0

        self.deltaX1 = 0.01
        self.deltaX2 = 0.01
        self.deltaXaux1_ini = 0
        self.deltaXaux2_ini = 0

    def read_forced_transitions(self):   
        try:                                                            # try/except used to handle errors
            with open(self.transfilename, 'r') as f:                    # open transitions file
                reader = csv.reader(f, delimiter='\t')                  # reader is a csv class to parse data files

                for L_item, R_item in reader:                           # L_item and R_item are the time stamps
                    self.transTimeL.append(float(L_item))               # append left time stamp to array
                    self.transTimeR.append(float(R_item))               # append left time stamp to array

        except EnvironmentError:                                        # except: if the file name is wrong
            print '{0} could not be opened'.format(self.transfilename)  # print error
            sys.exit()                                                  # exit python

    def reset_forced_values(self):
        self.i_R = 0
        self.i_L = 0
        self.Ron = 0
        self.Lon = 0
        self.timeTransR = self.transTimeL[0]
        self.timeTransL = self.transTimeR[0]
        self.deltaXaux1 = 0
        self.deltaXaux2 = 0

    def compute_forced_values(self, timeStartTrial, timeNow):
        if (timeNow - timeStartTrial > self.timeTransR) & (timeNow - timeStartTrial < self.timeTransR + self.timeRamp):
            self.deltaXaux1 = self.deltaX1 * (timeNow - timeStartTrial - self.timeTransR) / self.timeRamp
            self.Ron = 1
            
            if self.deltaXaux2_ini > self.deltaX2/2:
                self.deltaXaux2 = self.deltaX2 - self.deltaX2 * (timeNow - timeStartTrial - self.timeTransR) / self.timeRamp
            
            self.deltaXaux1_ini = self.deltaXaux1
            
        if (timeNow - timeStartTrial > self.timeTransR + self.timeRamp) & (self.Ron == 1):
            self.Ron = 0
            self.i_R = self.i_R + 1
            self.timeTransR = self.transTimeR[self.i_R]
            
        if (timeNow - timeStartTrial > self.timeTransL) & (timeNow - timeStartTrial < self.timeTransL + self.timeRamp):
            self.deltaXaux2 = self.deltaX2 * (timeNow - timeStartTrial - self.timeTransL) / self.timeRamp
            self.Lon = 1
            
            if (self.deltaXaux1_ini > self.deltaX1/2):
                self.deltaXaux1 = self.deltaX1 - self.deltaX1 * (timeNow - timeStartTrial - self.timeTransL) / self.timeRamp
            
            self.deltaXaux2_ini = self.deltaXaux2
        
        if (timeNow - timeStartTrial > self.timeTransL + self.timeRamp) & (self.Lon == 1):
            self.Lon = 0
            self.i_L = self.i_L + 1
            self.timeTransL = self.transTimeL[self.i_L]
        
        # update stereo value
        stereo1 = (-self.deltaXaux1/2 + self.deltaXaux2/2) * self.scale
        stereo2 =  (self.deltaXaux1/2 - self.deltaXaux2/2) * self.scale

        return stereo1, stereo2

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
        
        drawCircle(x0_pix, y0_pix, apertRad_pix, color)
        pass
    
    pass


