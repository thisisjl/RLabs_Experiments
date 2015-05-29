# Details for Plaid stimulus
**Execution**: python Plaid.py [optional name]. The optional name will be in the ouput data files, if no specified "defaultsubjectname" will be used.

**Input**: 
- config_file.txt (INI format, read using [Python's ConfigParser module](https://docs.python.org/2/library/configparser.html))
- trials_file.txt (INI format) 
- transitions_file.txt (only used with forced mode)

**Output**: data file for button presses and, if used, eyetracker data.
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