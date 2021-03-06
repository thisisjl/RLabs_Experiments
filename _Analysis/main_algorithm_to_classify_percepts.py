import os, sys
lib_path = os.path.abspath(os.path.join('..','_Libraries'))
sys.path.append(lib_path)
from rlabs_libutils import DataStruct, select_data, create_outlier_df, uniquelist_withidx
from rlabs_liblinreg import * 																# new library for the linear regression functions
import matplotlib.pyplot as plt
import numpy as np

# Define constants -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  
# constants for the outlier data frame:
outlier_threshold = 100  																	# velocity values over 100 will be outliers.
ambiguousoutlier_th = 80 																	# velocity values between 80 and 100 will be ambiguous outliers.
filter_samples = 5       																	# the samples following an outlier will not be outliers.

# constants for the linear regression:
minintervallen = 30																			# minimum number of samples an interval needs to be refined
thresrsq = 0.3 																				# r_squared threshold
thresslo = 0.0007 																			# slope threshold
btwpoints = 5 																				# method 1: minimum number of samples between ambiguous outliers
maxdivisions = 12 																			# method 2: maximum number of divisions applied to interval

# colors of plot:
a_color = 'gray' 																			# color of 'A' percept
b_color = 'lightgray' 																		# color of 'B' percept
c_color = 'tomato'																			# color of 'ambiguous' percept


# Read raw data and create outlier data frame -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  
path = select_data()
ds = DataStruct(path)

df = create_outlier_df(ds,outlier_threshold = outlier_threshold, ambiguousoutlier_th = ambiguousoutlier_th, 
	filter_samples = filter_samples)

# Compute linear regression  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  
outlier_idx = np.where(df['Outlierfiltered'])[0]   											# indexes where are outliers
amb_outlier_idx = np.where(df['isAmbiguousOutlier'])[0] 									# idexes where are ambiguous outliers
n = len(outlier_idx)-1 																		# number of outliers
lr_struct = [] 																				# initialize linear regression list (will be populates with dicts)

for i in range(n): 																			# for each outlier

	fit = regressionbtwpoints(df, outlier_idx[i], outlier_idx[i+1]) 						# compute the linear regression between an outlier and the next outlier
	fit = refineregression(fit, df, minintervallen = minintervallen, thresrsq = thresrsq, 
		thresslo = thresslo, btwpoints = btwpoints, maxdivisions = maxdivisions) 			# refine fit (will output fit if refinement not necessary)

	if type(fit) is list: 																	# if refinement outputs more than one segment
		for f in fit: 																		# get each segment 
			lr_struct.append(f) 															# and put it in array
	else: 																					# if only one segment (not refined)
		lr_struct.append(fit) 																# put it in array
	
	# write progress in terminal
	sys.stdout.write('\rComputing linear regression. {0} of {1} intervals'.format(i,n-1))
	sys.stdout.flush()


# figure 1: a) gaze position with reported and extracted percepts -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  
print '\nGenerating plot'
f, ax = plt.subplots(1, sharex = True)

ax.plot(df['time'], df['LEpos_int'], label = 'leftgazeX (interpolated)') 												# plot eye gaze
ax.set_title('Position trace (degrees)')

for event in ds.trial_ts:
    ax.plot((event, event), (np.min(df['LEpos_int']),np.max(df['LEpos_int'])), 'k-')									# line to indicate start and end of trial
for on, off in ds.A_ts:
    ax.axvspan(on, off, ymin=0.5, ymax=0.99, facecolor=a_color, linewidth=0, alpha=0.5, label = 'A percept') 			# reported percepts for a (button press)
for on, off in ds.B_ts:
    ax.axvspan(on, off, ymin=0.5, ymax=0.99, facecolor=b_color, linewidth=0, alpha=0.5, label = 'B percept') 			# reported percepts for b

for fit in lr_struct:
    on  = fit['start']
    off = fit['end']
    
    if fit['percept'] == 'A':
        pltcolor = a_color
        label = 'A percept'
    elif fit['percept'] == 'B':
        pltcolor = b_color
        label = 'B percept'
    else:
        pltcolor = c_color
        pltlabel = 'ambg percept'
    
    ax.axvspan(on, off, ymin=0.01, ymax=.5, facecolor=pltcolor, linewidth=0, alpha=0.5, label = pltlabel)

ax.set_ylabel("Extracted percepts | Reported percepts")

# Get artists and labels for legend of first subplot
handles, labels = ax.get_legend_handles_labels()
labelsidx, labels = uniquelist_withidx(labels)
ax.legend([handles[idx] for idx in labelsidx], labels)
ax.set_xlabel('time (ms)')

f.suptitle(ds.filename.split()[0])
plt.show()