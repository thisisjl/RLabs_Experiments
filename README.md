# RLabs Experiments 
Date started: April 2014
Date ended: ACTIVE

# Synopsis

Repository for Rlabs code.

Each "Experiment" folder contains a different visual stimulus, which are:
- **Plaid**: Pattern comprised of two superimposed gratings. When the plaid is set in motion, it becomes an ambiguous stimulus: it can be seen as one pattern moving in a single direction (coherence), or as two gratings, each moving in different directions with one sliding over the other (transparency). In prolonged viewing, the perception of moving plaids switches back and forth between the coherent and the transparent interpretation – a classic example of perceptual bistability.
- **Random dots kinematogram**: Pattern of n points randomly located in the window. The points within a distance R from the center are in motion and it becomes an ambiguous stimulus: it can be seen as one sphere rotating in left or right direction.
- **Calibration stimulus**: Simulates an eyetracker calibration stimulus. It will show a point in different locations depending on the number of points chosen.

All three stimuli are written using the pyglet library (www.pyglet.org) and are prepared to work with a Tobii eyetracker.

The folder **_Libraries** contains two libraries. **rlabs_libutils.py** contains common functions for all stimuli. **rlabs_libtobii.py** contains all the necessary functions to connect and commonicate with a Tobii eyetracker machine  (only Tobii X120 has been tested).

The folder **_Analysis** contains scripts to analyse and visualize eyetracker data and mouse press data.

# Required libraries
**For the stimuli** 
- Pyglet (http://www.pyglet.org/)
	- Installed using Python's pip: pip install pyglet
- Numpy (http://www.numpy.org/)
	- Installed the wheel file (numpy‑1.9.2+mkl‑cp27‑none‑win32.whl) from http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy and using pip install numpy‑1.9.2+mkl‑cp27‑none‑win32.whl
- Tobii SDK Python module (http://www.tobii.com/en/eye-tracking-research/global/landingpages/analysis-sdk-30/)
	- SDK version used: tobii-analytics-sdk-3.0.83-win-Win32
	- From the download, copy contents of SDK/Python27/Modules to Python/Lib/site-packages folder in your hard drive.
	- Not necessary if not using an eyetracker. If you do not install it, you will need to comment out the import of rlabs_libtobii.
- Pygtk (www.pygtk.org)
	- Install all-in-one version from http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/

**For the analysis code (interactiveplot.py)**
- Bokeh (http://bokeh.pydata.org/en/latest/)
	- Install the wheel file (bokeh‑0.8.2‑py27‑none‑any.whl
) from http://www.lfd.uci.edu/~gohlke/pythonlibs/#bokeh. 
	- Bokeh requires gevent (1.0.1‑cp27‑none‑win32.whl) I had to install it before separately because of the pip error "unable to find vcvarsall.bat".
	- Bokeh requires Matplotlib (http://matplotlib.org/).
	- Bokeh requires Scipy (http://www.scipy.org/).
	- Bokeh will install other libraries automatically.

# Details for Plaid stimulus
**Execution**: python Plaid.py [optional name]. The optional name will be in the ouput data files, if no specified "defaultsubjectname" will be used.

**Input**: config_file.txt, trials_file.txt (written in INI format, read using Python's ConfigParser module (https://docs.python.org/2/library/configparser.html))

**Output**: file for button presses data and, if used, eyetracker data.
- The format of the button press (event) data (7 + n columns, where n is the number of trials).
  - column 1: time stamp. Time when the event was recorded
  - column 2: event name. "InputEvent" for button presses, "TrialEvent" for start and end of trial.
  - column 3: event type. If InputEvent, "Mouse_DW" for mouse button press, "Mouse_UP" for mouse buttton release. If TrialEvent, number of trial.
  - column 4: event id. If InputEvent, number of the button pressed. If TrialEvent, START or END.
  - column 5: event code. Code used in analysis: 1 means LEFT button press, -1 LEFT button press. 4/-4 for RIGHT button. 8 is trial start, -8 is trial end.
  - column 6: event counter
  - column 7: parameters name. Name of parameters used
  - column 8 to 7+n: value of the parameter for each trial
- The eyetracker data contains 38 columns, the first one is the eyetracker time stamp (computed by its own clock), the rest of the colums are the different eye data that tobii offers in addition to the button press data.

# Motivation
# To do
# Short instructions
