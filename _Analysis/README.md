# _Analysis

**Synopsis**:
Collection of scripts used to analyze the responses of experimental subjects in the experiments.

# Description of files

- **interactiveplot.py**:

      Given a data file with eyetracker data, it will plot the eyetracker and the button press data over the different trials of the experiment.
      
      If there's no eyetracker data in the input file, only the button press data will be plot.
      
      For the first case, the plots will show along with the button presses, the X gaze coordinates, the Y gaze coordinates, the velocity for X and Y, and the XY gaze coordinates without button presses.
      
      The resulting graphs will be stored in a html file.
      
      It requires the library [Bokeh](bokeh.pydata.org)

- **main_algorithm_to_classify_percepts.py**:
      
      The purpose of this script is to extract percepts from the eyetracker data of a subject. The result is plotted using the format of Leopold-Fitzgibbons with reported and extracted percepts.

      In order to extract percepts, it is followed the algorithm in the schematic below:
      ![alt tag](http://i.imgur.com/qgSPVQa.jpg) 


- **comparingfilters.py**:

      Temporal script to compare, using different parameters, the Savitzky-Golay filter, the Differential filter and the Hayashi filter.

- **show_button_press_over_eye_outliers.py**:

      Temporal script to display the eye outliers compared to the button presses over time.

- **PreProcessingEyeData**:

- **AnalyzeButtonPresses**:

