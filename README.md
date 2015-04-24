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
Using Python 2.7 because the tobii skd only supports python 2.7.


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

# Motivation
# To do
# Short instructions
