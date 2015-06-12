import math                         # for the circle
from pyglet.gl import *             # for the circle
import time                         # for the update method of the gratings
import csv                          # for reading the forced transition file
import os, stat                     # to create read-only file
import numpy as np                  # for camera sin and cos
from pyglet.window import key,mouse # for event handler
# import scipy as sp                  # for SNR in DataStruct()
import scipy.stats 
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

def movingaverage(array, samples):
    window = np.ones(int(samples))/float(samples)
    return np.convolve(array, window, 'valid')

def differentialsmoothing(array, bins, divisor, fs = 120.0):
    window = np.hstack((-np.ones(bins),0,np.ones(bins)))
    return np.convolve(array, window, 'valid') / (divisor / fs)

def is_outlier(points, thresh=3.5):
    """
    Returns a boolean array with True if points are outliers and False 
    otherwise.

    Parameters:
    -----------
        points : An numobservations by numdimensions array of observations
        thresh : The modified z-score to use as a threshold. Observations with
            a modified z-score (based on the median absolute deviation) greater
            than this value will be classified as outliers.

    Returns:
    --------
        mask : A numobservations-length boolean array.

    References:
    ----------
        Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and
        Handle Outliers", The ASQC Basic References in Quality Control:
        Statistical Techniques, Edward F. Mykytka, Ph.D., Editor. 
    
    Got it from:
    ------------
    http://stackoverflow.com/questions/11882393/matplotlib-disregard-outliers-when-plotting
    """
    if len(points.shape) == 1:
        points = points[:,None]
    median = np.median(points, axis=0)
    diff = np.sum((points - median)**2, axis=-1)
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)

    modified_z_score = 0.6745 * diff / med_abs_deviation

    return modified_z_score > thresh

def rgb2hex(color):

    if max(color) <= 1:
        color = (np.array(color) * 255).astype(int).tolist()
    
    r = max(0, min(color[0] , 255))
    g = max(0, min(color[1] , 255))
    b = max(0, min(color[2] , 255))

    return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)

def filechooser(title = 'Select files', initialdir = ''):
    import pygtk
    pygtk.require('2.0')

    import gtk

    # Check for new pygtk: this is new class in PyGtk 2.4
    if gtk.pygtk_version < (2,3,90):
       print "PyGtk 2.3.90 or later required for this example"
       raise SystemExit

    dialog = gtk.FileChooserDialog(title,
                                   None,
                                   gtk.FILE_CHOOSER_ACTION_OPEN,
                                   (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    dialog.set_default_response(gtk.RESPONSE_OK)
    dialog.set_current_folder(initialdir)

    filter = gtk.FileFilter()
    filter.set_name("All files")
    filter.add_pattern("*")
    dialog.add_filter(filter)

    filter = gtk.FileFilter()
    filter.set_name("Data file")
    filter.add_pattern("*.txt")
    filter.add_pattern("*.dat")
    dialog.add_filter(filter)

    response = dialog.run()
    if response == gtk.RESPONSE_OK:
        # print dialog.get_filename(), 'selected'
        pass
    elif response == gtk.RESPONSE_CANCEL:
        print 'Closed, no files selected'
    
    return dialog.get_filename()
    
    dialog.destroy()

def px2deg(px_val, h = 25, d = 60, r = 768):
    """
        Convert a value in pixels (px_val) to degrees (deg_val).
        from: http://osdoc.cogsci.nl/miscellaneous/visual-angle/

        h: Monitor height in cm
        d: Distance between monitor and participant in cm
        r: Vertical resolution of the monitor
    """
    # Calculate the number of degrees that correspond to a single pixel. This will
    # generally be a very small value, something like 0.03.
    deg_per_px = np.degrees(np.arctan2(.5*h, d)) / (.5*r)

    # Convert value from pixes to degrees
    deg_val = px_val * deg_per_px

    return deg_val

def deg2px(deg_val, h = 25, d = 60, r = 768):
    """
        Convert a value in degrees (deg_val) to pixels (px_val).
        from: http://osdoc.cogsci.nl/miscellaneous/visual-angle/

        h: Monitor height in cm
        d: Distance between monitor and participant in cm
        r: Vertical resolution of the monitor
    """
    # Calculate the number of degrees that correspond to a single pixel. This will
    # generally be a very small value, something like 0.03.
    deg_per_px = np.degrees(np.arctan2(.5*h, d)) / (.5*r)

    # Calculate the size of the stimulus in degrees
    px_val = deg_val / deg_per_px

    return px_val

def select_data():
    from Tkinter import Tk                                          # for open data file GUI
    from tkFileDialog import askopenfilenames                       # for open data file GUI
    Tk().withdraw()                                                 # we don't want a full GUI, so keep the root window from appearing
    datafile = askopenfilenames(title='Choose file',                # show an "Open" dialog box and return the path to the selected file
        initialdir = '..')[0] 
    return datafile

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
        self.leftvalidity   = []            #
        self.leftpupil      = []            #
        self.rightgazeX     = []            # 
        self.rightgazeY     = []            # 
        self.rightvalidity  = []            #
        self.rightpupil     = []            #

        self.leftgazeXvelocity  = []        # to allocate velocity
        self.rightgazeXvelocity = []        # which will be computed
        self.leftgazeYvelocity  = []        # in self.read_data()
        self.rightgazeYvelocity = []        #

        self.dataloss   = []                # store data loss information
        self.snr        = []                # store snr
        self.cv         = []                # store coefficient of variation


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

        self.order = []                     # number of the trials from the trials_file.txt in the order they appeared
      

        self.read_data()                    # read data

        self.expname = ''
        self.subjectname = ''

    def read_data(self):
        # read data. try/except for reading different formats -------------------------------------------------------------------------------------------------
        self.filename = os.path.split(self.filenamefp)[1]                                           # get just data file name, not full path
        try:
            data = np.genfromtxt(self.filenamefp, delimiter="\t",                                   # read data file, dtype allows mixed types of data,
            dtype=None, names=True, usecols = range(38))                                            # names reads first row as header, usecols will read just 38 columns
            print '{0}: eyetracker data (38 colums format)'.format(os.path.split(self.filename)[1])
        except ValueError:                                                                          
            try:                                                                                    # if file does not have 38 columns, try 
                data = np.genfromtxt(self.filenamefp, delimiter="\t", 
                    dtype=None, names=True, usecols = range(34))                                    # 34 colums (legacy file)
                print '{0}: eyetracker data (34 colums format). This does not have parameters'.format(os.path.split(self.filename)[1])
            except ValueError:
                try:
                    data = np.genfromtxt(self.filenamefp, delimiter="\t",                           # if that stil does not work
                    dtype=None, names=True, usecols = range(6))                                     # try with 6 colums (only button presses file, no parameters)
                    print '{0}: button press data'.format(os.path.split(self.filename)[1])
                except ValueError:                                                                  # if neither of these work, 
                    print 'cannot read data file {0}'.format(os.path.split(self.filenamefp)[1])     # cannot read data file
                    sys.exit()

        # Determine if datafile contains eyetracker data or just input (mouse) ----------------------------------------
        et_data = True if 'LeftGazePoint2Dx' in data.dtype.names else False                         # if LeftGazePoint2Dx in header, et_data is True, else is False

        
        # Read events data --------------------------------------------------------------------------------------------
        if et_data:
            try:
                ets       = data['EventTimeStamp'][data['EventTimeStamp']!='-'].astype(np.float)    # event time stamp: filter out values with '-' and convert str to float
                ecode     = data['Code'][data['Code'] != '-'].astype(np.float)                      # event code: filter out values with '-' and convert to float
            except ValueError:
                print data.dtype.names
        else:
            try:
                if '-' in data['EventTimeStamp']:
                    ets       = data['EventTimeStamp'][data['EventTimeStamp']!='-'].astype(np.float)# event time stamp
                    ecode     = data['Code'][data['Code'] != '-'].astype(np.float)                 # event code
                else:
                    ets       = data['EventTimeStamp']                                             # event time stamp
                    ecode     = data['Code']                                                       # event code
            except ValueError:
                print 'except'
                ets       = data['Timestamp']                                                       # event time stamp
                ecode     = data['EventCode']                                                       # event code
        # print data['Code']

        Trial_on  = ets[ecode ==  self.trial_code]                                                  # get timestamp of trials start
        Trial_off = ets[ecode == -self.trial_code]                                                  # get timestamp of trials end

        A_on      = ets[ecode ==  self.A_code]                                                      # get timestamp of percept A on (LEFT press)
        A_off     = ets[ecode == -self.A_code]                                                      # get timestamp of percept A off (LEFT release)

        B_on      = ets[ecode ==  self.B_code]                                                      # get timestamp of percept B on (RIGHT press)
        B_off     = ets[ecode == -self.B_code]                                                      # get timestamp of percept B off (RIGHT release)

        self.numtrials = len(Trial_on)                                                              # compute number of trials
        self.order  = data['EventType'][ecode ==  self.trial_code]                                  # number of the trials from the trials_file in the order they appeared

        # datastruct
        self.trial_ts = np.empty((Trial_on.size + Trial_off.size,), dtype=Trial_on.dtype)           # create empty matrix of specific lenght
        self.trial_ts[0::2] = Trial_on                                                              # put Trial_on on even spaces 
        self.trial_ts[1::2] = Trial_off                                                             # put Trial_off on odd spaces

        # Check input events --------------------------------------------------------------------------------------------

        # Get input in each trial
        x, y, z = 2, 0, self.numtrials                                                              # size of percept matrix
        self.A_trial = [[[0 for k in xrange(x)] for j in xrange(y)] for i in xrange(z)]             # matrix for A percept of each trial
        self.B_trial = [[[0 for k in xrange(x)] for j in xrange(y)] for i in xrange(z)]             # matrix for B percept of each trial

        for trial in range(self.numtrials):                                                         # for each trial
            start = self.trial_ts[2 * trial]                                                        # timestamp start of trial
            end   = self.trial_ts[2 * trial + 1]                                                    # timestamp end of trial

            A_on_in_trial = [i for i in A_on if start<i<end]                                        # get A_on in trial

            for ts_on in A_on_in_trial:                                                             # for each A_on
                val, idx_start = find_nearest_above(A_off, ts_on)                                   # look for the nearest above A_off
                
                if val is not None:                                                                 # compare nearest above to end of trial,
                    ts_off = np.minimum(end,val)                                                    # get minimum                                               
                else:
                    ts_off = end

                self.A_trial[trial].append([ts_on, ts_off])                                         # add A_on and A_off times to percept matrix

            B_on_in_trial = [i for i in B_on if start<i<end]                                        # get A_on in trial

            for ts_on in B_on_in_trial:                                                             # for each B_on
                val, idx_start = find_nearest_above(B_off, ts_on)                                   # look for the nearest above B_off
                
                if val is not None:                                                                 # compare nearest above to end of trial,
                    ts_off = np.minimum(end,val)                                                    # get minimum
                else:
                    ts_off = end

                self.B_trial[trial].append([ts_on, ts_off])                                         # add B_on and B_off times to percept matrix

            for item in self.A_trial[trial]:                                                        # datastruct.A/B_ts will contain on and off
                self.A_ts.append(item)                                                              # time staps in the following way:
            for item in self.B_trial[trial]:                                                        # [[on_1, off_2], [on_2, off_2] ...]
                self.B_ts.append(item)                                                              # 

        # Read eyetracker data ---------------------------------------------------------------------------------------
        if et_data:
            self.eyetrackerdata = True                                                              # indicate that datastruct contains eyetracker data

            self.timestamps     = np.array(map(float, data['Timestamp']))                           # get time stamps of the eye tracker data

            self.leftgazeX      = np.array(map(float, data['LeftGazePoint2Dx']))                    # get left gaze X data
            self.leftgazeY      = np.array(map(float, data['LeftGazePoint2Dy']))                    # get left gaze Y data
            self.leftvalidity   = np.array(map(float, data['LeftValidity']))                        # get left gaze validity
            self.leftpupil      = np.array(map(float, data['LeftPupil']))                           # get left pupil size
            
            self.rightgazeX     = np.array(map(float, data['RightGazePoint2Dx']))                   # get right gaze X data
            self.rightgazeY     = np.array(map(float, data['RightGazePoint2Dy']))                   # get right gaze Y data
            self.rightvalidity  = np.array(map(float, data['RightValidity']))                       # get right gaze validity
            self.rightpupil     = np.array(map(float, data['RightPupil']))                          # get right pupil size

            self.vergence       = np.array(map(float, data['Vergence']))                            # get vergence
            self.fixationdist   = np.array(map(float, data['FixationDist']))                        # get fixation distance

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
            leftgazeX_pix  = self.leftgazeX  * self.winwidth_pix                                    #
            rightgazeX_pix = self.rightgazeX * self.winwidth_pix
            leftgazeY_pix  = self.leftgazeY  * self.winwidth_pix
            rightgazeY_pix = self.rightgazeY * self.winwidth_pix

            # 2 - convert gaze values from pixels to degrees
            V = 2 * np.arctan(self.winwidth_cm/2 * self.fixdist)                                    # in radians
            deg_per_pix = V / self.winwidth_pix                                                     # in degrees

            leftgazeX_deg  = leftgazeX_pix  * deg_per_pix                                           #
            rightgazeX_deg = rightgazeX_pix * deg_per_pix                                           #
            leftgazeY_deg  = leftgazeY_pix  * deg_per_pix                                           #
            rightgazeY_deg = rightgazeY_pix * deg_per_pix                                           #

            # 3 - compute velocity
            self.leftgazeXvelocity  = np.diff(leftgazeX_deg,  n=1) * self.framerate;                #
            self.rightgazeXvelocity = np.diff(rightgazeX_deg, n=1) * self.framerate;                #
            self.leftgazeYvelocity  = np.diff(leftgazeY_deg,  n=1) * self.framerate;                #
            self.rightgazeYvelocity = np.diff(rightgazeY_deg, n=1) * self.framerate;                #


            # For each trial, compute percentage of validity, 
            # Signal to Noise Ratio (SNR) and coefficient of variation (CV)

            self.dataloss   = []                                                                    # to store data loss percentage
            self.snr        = [['LeftGazeX','RightGazeX','LeftGazeY','RightGazeY']]                 # to store SNR
            self.cv         = [['LeftGazeX','RightGazeX','LeftGazeY','RightGazeY']]                 # to store CV

            for trial in range(self.numtrials):                                                     # for each trial
                start = self.trial_ts[2 * trial]                                                    # timestamp start of trial
                end   = self.trial_ts[2 * trial + 1]                                                # timestamp end of trial

                val, idx_start = find_nearest_above(self.timestamps, start)                         # get array index for start of trial
                val, idx_end   = find_nearest_above(self.timestamps, end)                           # get array index for end of trial
                if idx_end is None: idx_end = len(self.timestamps)-1                                # if end of trial was end of experiment

                nsamples = idx_end - idx_start                                                      # number of samples in trial

                lgx = self.leftgazeX[idx_start:idx_end]
                rgx = self.rightgazeX[idx_start:idx_end]
                lgy = self.leftgazeY[idx_start:idx_end]
                rgy = self.rightgazeY[idx_start:idx_end]
                lv  = self.leftvalidity[idx_start:idx_end]
                rv  = self.rightvalidity[idx_start:idx_end]

                # compute percentage of validity
                lv_trial = 100 * (self.leftvalidity[idx_start:idx_end] == 4).sum()/float(nsamples)  # left eye:  % of lost data
                rv_trial = 100 * (self.rightvalidity[idx_start:idx_end] == 4).sum()/float(nsamples) # right eye: % of lost data

                self.dataloss.append([lv_trial, rv_trial])                                          # store % of lost data

                # compute SNR
                lx_snr = scipy.stats.signaltonoise(lgx[lv != 4])
                rx_snr = scipy.stats.signaltonoise(rgx[rv != 4])
                ly_snr = scipy.stats.signaltonoise(lgy[lv != 4])
                ry_snr = scipy.stats.signaltonoise(rgy[rv != 4])
                self.snr.append([lx_snr, rx_snr, ly_snr, ry_snr])

                # compute variation
                lx_cv = scipy.stats.variation(lgx[lv != 4])
                rx_cv = scipy.stats.variation(rgx[rv != 4])
                ly_cv = scipy.stats.variation(lgy[lv != 4])
                ry_cv = scipy.stats.variation(rgy[rv != 4])
                self.snr.append([lx_cv, rx_cv, ly_cv, ry_cv])

                print 'Trial {0} - {1} % of data was lost. SNR: {2}. CV: {3}'.format(trial + 1,      # report data loss, snr and cv
                    "%.1f" % lv_trial, lx_snr, lx_cv)    

def write_data_file_with_parameters(data_namefile, data_struct, parameters, right_keys = [4], left_keys = [1], codes = [1, 4, 8, 999]):
    """ write data file including events (mouse, trials) and configuration and trials parameters"""
    from itertools import izip_longest                                  # import itertools to iterate over two variables
    from collections import OrderedDict                                 # for the parameters by trials dictionary

    if parameters: 
        ntrials = int(parameters['numtrials'])                          # get number of trials
    else:
        ntrials = 0

    # order parameters by the order of trials --------------------------
    trialsorder = parameters['trialsorder']                             # get order of trials
    prmtsbytrials = OrderedDict()                                       # parameters ordered by trial order
    for k,v in parameters.items():                                      # for each parameter
        if type(v) == list and not 'color' in k:                        # if it is a list and it is not a color
            prmtsbytrials[k] = [(v[i] if type(v) == list else v)\
                for i in trialsorder]                                   # order it
        else:                                                           # if it is a color, int or float,
            prmtsbytrials[k] = v                                        # copy it as it is
        prmtsbytrials['trialsorder'] = sorted(
            np.array(parameters['trialsorder']) + 1)                    # put sorted trials order

    timeStampStart = data_struct[0].timestamp                           # get time stamp of the start of trial 1

    fields = ['EventTimeStamp', 'EventName', 'EventType', 'EventID',    # create header
    'Code', 'TrialsCount', 'Parameters']

    for n in range(ntrials):                                            # for each trial
        fields.append('Value-trial-{0}'.format(n+1))                    # add field in header 
   
    with open(data_namefile, 'w' ) as f:                                # open or create text file 'data_namefile' to write
        f.write('\t'.join(fields)+'\n')                                 # write header. Separate the fields with tabs

        for e, b in izip_longest(data_struct, prmtsbytrials.items()):   # iterate over data_struct and parameters until longest is over
        
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


# Analysis functions ------------------------------------------------------------------------------------------------

def gentimeseries(timestamps, percepts):
    """
        Generate a time series array of percepts
        input:
            timestamps: array 1xN containing time stamps at a constant sampling rate, where N is the number of samples.
                        In our case, it is the array of the eyetracker time stamps (DataStruct.timestamps).
            percepts:   array Mx2 containing time stamps indicating the start and the end of a percept.
                        In our case, it is the array with the button presses (DataStruct.A_ts for a complete experiment, ds.A_trial[i] for trial i and percept A)
        output:
            timeseries: boolean array 1xN, it is 1 when the percept was on, 0 otherwise.
    """
    on  = []
    off = []
    
    for p in percepts:
        val_on,  idx_on  = find_nearest_above(timestamps,p[0])
        val_off, idx_off = find_nearest_above(timestamps,p[1])
        if idx_off is None: idx_off = len(timestamps)
        on.append(idx_on)
        off.append(idx_off)
        
    timeseries = np.zeros(len(timestamps))
    for i in range(len(on)):
        timeseries[on[i]:off[i]] = 1
    
    return timeseries

def gencontinuousoutliers(Aoutliers, Boutliers):
    """
        Generate a continuous Aoutlier array
        
        input:
            Aoutliers, Boutliers
                boolean arrays indicating percept (A or B) outliers in eyetracker data
        output:
            c
                will be 1 starting when Aoutliers is 1 until when Boutliers is 1
    """
    from itertools import izip                  # izip to iterate over two arrays until shortest ends
    
    c = np.zeros(len(Aoutliers),dtype=int)      # initialize output array

    idxa = np.where(Aoutliers==1)[0]            # get indices when A is 1
    idxb_tmp = np.where(Boutliers==1)[0]        # get indices when B is 1 (temporal variable)

    idxb = []                                   # initialize array
    for ia in idxa:                             # for each index of A outlier
        val,idx = find_nearest_above(idxb_tmp,ia)   # get B outlier above it
        idxb.append(val)                        # append value to array

    for ia, ib in izip(idxa,idxb):              # for each index
        c[ia:ib] = 1                            # set c to 1
    
    return c                                    # return

def filteroutliers(array, samples = 2):
    """
        Given a boolean array, filteroutliers will turn to FALSE those
        values that are in within 'samples' distance from a TRUE value.
        - a:       boolean array
        - samples: integer
    """
    import numpy as np

    out = np.zeros(array.size, dtype = bool)            # initialize output array, all set to False
    s = 0                                               # initialize samples counter
    startcounting = 0                                   # do not start counting samples yet

    for idx, val in enumerate(array):                   # for each item in array, get index and value
        if val == True and s == 0:                      # if value is True and counter is 0
            out[idx] = True                             # set output at idx to True
            startcounting = 1                           # and enable counting samples
            
        if startcounting: s += 1                        # count samples
              
        if s == samples + 1:                            # if s counter is bigger than samples, 
            s = 0                                       # reset counter
            startcounting = 0                           # do not count

    return out                                          # return output array

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
        self.prev_events_len = 0

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
        self.bar_length   = 1000

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

        radio_aux = (2 * self.apertRad_pix) + self.mylambda #diameter 
        num_bars = int(1 + math.floor(radio_aux / self.mylambda)) + 3
       
        glStencilFunc (GL_EQUAL, 0x1, 0x1) 
        glStencilOp (GL_KEEP, GL_KEEP, GL_KEEP)
             
        glLoadIdentity() #replace current matrix with the identity matrix
        glTranslatef(self.x, self.y, 0)
        glRotatef(self.orientation,0,0,1)    
        glTranslatef(-self.x, -self.y, 0)
     
        glColor3f(self.fill_color[0] , self.fill_color[1], self.fill_color[2] )
         
        glBlendFunc(GL_ZERO, GL_SRC_COLOR)  
         
        for i in range(int(-num_bars/2),int(num_bars/2)):    
             
            x1 = self.mylambda * i + self.x
            x2 = (self.duty_cycle * self.mylambda) + (self.mylambda * i + self.x)
             
            glBegin(GL_QUADS)
             
            glVertex2f(x1, self.y - self.bar_length) 
            glVertex2f(x1, self.y + self.bar_length) 
            glVertex2f(x2, self.y + self.bar_length) 
            glVertex2f(x2, self.y - self.bar_length)
             
            glEnd()
         
        # glRotatef(-orientation, 0, 0, 1)#Is it necessary?
        #glBlendFunc(GL_ONE, GL_ZERO) #150116 comment out NR
        glLoadIdentity()
        pass
     
    def update_position(self, runningTime, stereo):

        timeNow = time.time()

        position = self.initialpos + stereo

        self.x = position + math.fmod(self.speed*(timeNow-runningTime), self.motion_cycle)
        # if self.orientation < self.threshold_angle:
        #     self.x = position + math.fmod(speed*(timeNow-runningTime), motion_cycle)
        # elif self.orientation >= self.threshold_angle:
        #     self.y = initialpos + math.fmod(speed*(timeNow-runningTime), motion_cycle)


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

class _Forced_struct():
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

class Forced_struct():
    def __init__(self, transfilename = 'forcedtransitions.txt', timeRamp = 0.5, scale = 500):
        from collections import OrderedDict                             # to get the order without duplicates

        self.transfilename = transfilename                              # get transitions file name
        self.timeRamp = timeRamp                                        # get stereo speeed
        self.scale = scale
        self.transTimeL = []                                            # initialize Left  timestamps array
        self.transTimeR = []                                            # initialize Right timestamps array
        self.transTrial = []
        self.transOrder = []

        self.stereo1 = 0
        self.stereo2 = 0

        self.read_forced_transitions()                                  # read transition time stamps
        
        #self.order = list(OrderedDict.fromkeys(self.order))             # get order without duplicates

        # initialize forced variables
        self.reset_forced_values(trial = 0)

        self.deltaX1 = 0.01
        self.deltaX2 = 0.01
        self.deltaXaux1_ini = 0
        self.deltaXaux2_ini = 0

    def OLD_read_forced_transitions(self):   
        try:                                                            # try/except used to handle errors
            with open(self.transfilename, 'r') as f:                    # open transitions file
                reader = csv.reader(f, delimiter='\t')                  # reader is a csv class to parse data files

                for L_item, R_item, trial, order in reader:             # L_item and R_item are the time stamps
                    if L_item != 'None':
                        self.transTimeL.append(float(L_item))           # append left time stamp to array
                    else:
                        self.transTimeL.append(np.nan)                  # append left time stamp to array
                    if R_item != 'None':
                        self.transTimeR.append(float(R_item))           # append right time stamp to array
                    else:
                        self.transTimeR.append(np.nan)                  # append right time stamp to array
                    self.transTrial.append(int(trial))                  # append trial number to array

                    self.order.append(int(order))                            # append order number to array

        except EnvironmentError:                                        # except: if the file name is wrong
            print '{0} could not be opened'.format(self.transfilename)  # print error
            sys.exit()                                                  # exit python

    def read_forced_transitions(self):
        """
            takes into account header formatting:
            format: sptrial  L_item   R_item  sptrial2    ptrial
                sptrial: number of trial from spontaneos experiment
                L_item: left on time stamp
                R_item: right on time stamp
                sptrial2: number of trial from spontaneos experiment 
                ptrial: prameters from the trial in trials_file.txt
        """

        try:
            with open(self.transfilename,'r') as f:                     # open transitions file
                reader = csv.reader(f,delimiter='\t')                   # read it with csv
                headers = reader.next()                                 # ignore headers
                
                for sptrial, L_item, R_item, sptrial2, ptrial in reader:# for each item in file
                    if L_item != 'None':                                # if Left is not none,
                        self.transTimeL.append(float(L_item))           # append left time stamp to array
                    else:
                        self.transTimeL.append(np.nan)                  # put a nan otherwise
                    
                    if R_item != 'None':                                # if right is not none,
                        self.transTimeR.append(float(R_item))           # append right time stamp to array
                    else:
                        self.transTimeR.append(np.nan)                  # put a nan otherwise
                    
                    self.transTrial.append(int(sptrial))                # append trial number to array

                    self.transOrder.append(int(ptrial))                 # append order number to array

        except EnvironmentError:
            print '{0} could not be opened'.format(self.transfilename)  # print error
            sys.exit()                                                  # exit python

    def reset_forced_values(self, trial = 0):
        self.get_values_for_trial(trial)
        self.trial = trial

        self.i_R = 0
        self.i_L = 0
        self.Ron = 0
        self.Lon = 0
        self.timeTransR = self.transTimeL_trial[0]
        self.timeTransL = self.transTimeR_trial[0]
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
            if self.i_R < len(self.transTimeR_trial):
                self.timeTransR = self.transTimeR_trial[self.i_R]
           
        if (timeNow - timeStartTrial > self.timeTransL) & (timeNow - timeStartTrial < self.timeTransL + self.timeRamp):
            self.deltaXaux2 = self.deltaX2 * (timeNow - timeStartTrial - self.timeTransL) / self.timeRamp
            self.Lon = 1
            
            if (self.deltaXaux1_ini > self.deltaX1/2):
                self.deltaXaux1 = self.deltaX1 - self.deltaX1 * (timeNow - timeStartTrial - self.timeTransL) / self.timeRamp
            
            self.deltaXaux2_ini = self.deltaXaux2
        
        if (timeNow - timeStartTrial > self.timeTransL + self.timeRamp) & (self.Lon == 1):
            self.Lon = 0
            self.i_L = self.i_L + 1
            if self.i_L < len(self.transTimeL_trial):
                self.timeTransL = self.transTimeL_trial[self.i_L]
       
        # update stereo value
        self.stereo1 = (-self.deltaXaux1/2 + self.deltaXaux2/2) * self.scale
        self.stereo2 =  (self.deltaXaux1/2 - self.deltaXaux2/2) * self.scale

        # print '{3}\t{0}\t{1}\t{2}'.format(timeNow - timeStartTrial,stereo1,stereo2,self.trial)
        # print '{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}\t{10}\t{11}\t{12}\t{13}'.format(
        #     self.trial, timeNow - timeStartTrial, stereo1, stereo2, self.i_R, self.i_L, self.Ron, self.Lon, 
        #     self.timeTransR, self.timeTransL, self.deltaXaux1, self.deltaXaux2, self.deltaXaux1_ini, self.deltaXaux2_ini)

    def get_values_for_trial(self, trial = 0):
        idx_trial = np.where(np.array(self.transTrial) == trial)[0]
        self.transTimeL_trial = np.array(self.transTimeL)[idx_trial]
        self.transTimeR_trial = np.array(self.transTimeR)[idx_trial]

    def reset_forced_values_in_order(self, trial = 0):
        self.get_values_for_trial_in_order(trial)
        self.trial = trial

        self.i_R = 0
        self.i_L = 0
        self.Ron = 0
        self.Lon = 0
        self.timeTransR = self.transTimeL_trial[0]
        self.timeTransL = self.transTimeR_trial[0]
        self.deltaXaux1 = 0
        self.deltaXaux2 = 0

    def get_values_for_trial_in_order(self, trial = 0):
        idx_trial = np.where(np.array(self.transOrder) == trial)[0]
        self.transTimeL_trial = np.array(self.transTimeL)[idx_trial]
        self.transTimeR_trial = np.array(self.transTimeR)[idx_trial]

def create_transitions_file(infilename = None, outfilename = None, A_code = 1, B_code = 4, trial_code = 8, relative = 1, min_dur = 0.3):
    from itertools import izip_longest

    ds = DataStruct(infilename, A_code = A_code, B_code = B_code, trial_code = trial_code)  # read data and put it in datastruct format

    # compute durations for each trial
    A_dur = []
    B_dur = []

    x, y, z = 2, 0, ds.numtrials                                                            # size of percept matrix
    A_dur_trial = [[[] for j in xrange(y)] for i in xrange(z)]                              # matrix for A percept of each trial 
    B_dur_trial = [[[] for j in xrange(y)] for i in xrange(z)]                              # matrix for B percept of each trial

    output_array = []                                                                       # initialize array to write in outfilename

    sumdurA = 0
    sumdurB = 0
    sumdurA_trial = []
    sumdurB_trial = []

    for trial in range(ds.numtrials):

        start = ds.trial_ts[2 * trial]                                                      # timestamp start of trial
        end   = ds.trial_ts[2 * trial + 1]                                                  # timestamp start of trial

        for a in ds.A_trial[trial]:                                                         # compute A durations in trial
            dur = a[1] - a[0]
            sumdurA += dur
            a_on = a[0] - start if relative else a[0]                                       # time stamp of A_on event relative to start of trial 
            if dur > min_dur: 
                A_dur.append([dur, a_on, trial])
                A_dur_trial[trial].append([dur,a_on, trial])
        
        for b in ds.B_trial[trial]:                                                         # compute B durations in trial
            dur = b[1] - b[0]
            sumdurB += dur
            b_on = b[0] - start if relative else b[0]                                       # time stamp of B_on event relative to start of trial
            if dur > min_dur: 
                B_dur.append([dur, b_on, trial])
                B_dur_trial[trial].append([dur, b_on, trial])

        if abs(len(A_dur) - len(B_dur)) > 3:
            print 'Trial {0}. Large difference in number of A and B durations'.format(trial)
            print 'Length of A durations is {0}'.format(A_dur)
            print 'Length of B durations is {0}\n'.format(B_dur)

        sumdurA_trial.append(sumdurA)
        sumdurB_trial.append(sumdurB)

        if sumdurA + sumdurB > (end - start):
            print 'Warning: summed durations more than expected in Trial {0}'.format(trial)
            print 'sumdurA + sumdurB = {0}'.format(sumdurA + sumdurB)
            print 'end - start = {0}\n'.format(end - start)
                   
        # write durations of A and B of this trial to output array -------------------------
        if A_dur_trial[trial] != [] and B_dur_trial[trial] != []:                           # if there are percepts for A and B in this trial,                         
            for a, b in izip_longest(np.array(A_dur_trial[trial])[:,1],                     # write them
                np.array(B_dur_trial[trial])[:,1]):
                output_array.append([a,b,trial,ds.order[trial]])
        
        elif A_dur_trial[trial] == [] and B_dur_trial[trial] != []:                     # if there are no precepts for A in this trial,
            for b in np.array(B_dur_trial[trial])[:,1]:                                     # just write the ones that are of B
                output_array.append([None,b,trial,ds.order[trial]])
        
        elif B_dur_trial[trial] == [] and A_dur_trial[trial] != []:                         # if there are no precepts for B in this trial,
            for a in np.array(A_dur_trial[trial])[:,1]:                                     # just write the ones that are for A
                output_array.append([a,None,trial,ds.order[trial]])
                
    with open(outfilename, 'w' ) as f:                                                      # open or create text file 'outfilename' to write
        fields = ['Spontaneous trial', 'L_item', 'R_item', 'trial (timestamp from)', 'trial (parameters from)']
        f.write('\t'.join(fields)+'\n')                                                     # write header. Separate the fields into tabs
        for out in output_array:                                                            # write contents of output_array:
            f.write('{2}\t{0}\t{1}\t{2}\t{3}\n'.format(out[0],out[1],out[2],out[3]))             #

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


