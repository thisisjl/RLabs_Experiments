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

The folder "_Libraries" contains two libraries. "rlabs_libutils.py" contains common functions for all stimuli. "rlabs_libtobii.py" contains all the necessary functions to connect and commonicate with a Tobii eyetracker machine  (only Tobii X120 has been tested).

The folder "_Analysis" contains scripts to analyse and visualize eyetracker data and mouse press data.

# Details
# Motivation
# To do
# Short instructions
# Required libraries
