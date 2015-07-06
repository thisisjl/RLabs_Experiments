import os, sys
lib_path = os.path.abspath(os.path.join('..','_Libraries'))
sys.path.append(lib_path)
from rlabs_libutils import DataStruct, select_data, create_outlier_df
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from itertools import izip

# read raw data 
path = select_data()
ds = DataStruct(path)

# define constants
outlier_threshold = 120
ambiguousoutlier_th = 100
filter_samples = 5

# create outlier DataFrame
df = create_outlier_df(ds, outlier_threshold = outlier_threshold,
	ambiguousoutlier_th = ambiguousoutlier_th, filter_samples = filter_samples)

# Compute linear regression of Gaze position between outliers
outlier_idx = np.where(df['Outlierfiltered'])[0]
slope_array = []
intercept_array = []
r_value_array = []
n = len(outlier_idx)-1
for i in range(n):
    lr_idx = np.arange(outlier_idx[i],outlier_idx[i+1])   # linear regression idx. outlier and next outlier
    slope, intercept, r_value, p_value, std_err = stats.linregress(df['time'][lr_idx], df['LEpos_int'][lr_idx])
    
    slope_array.append(slope)
    intercept_array.append(intercept)
    r_value_array.append(r_value)
    
r_squared_array = np.power(r_value_array,2)

# ------------------------------------------------------------------------------------------------------------
# Plot: a) eye gaze with linear regression and r squared values, b) velocity with outliers
f, ax = plt.subplots(2, sharex = True)
ax[0].plot(df['time'], df['LEpos_int'])

for i in range(n):
    ax[0].plot(df['time'][outlier_idx[i:i+2]], slope_array[i]*df['time'][outlier_idx[i:i+2]] + intercept_array[i], 'r')
    
    # compute annotation coordinates (where the r squared values will show)
    x = df['time'][outlier_idx[i]] + np.diff(df['time'][outlier_idx[i:i+2]])[0]/2.0
    y = np.diff(slope_array[i]*df['time'][outlier_idx[i:i+2]] + intercept_array[i])[0]/2.0
    ax[0].annotate('{0}'.format("%.2f" % r_squared_array[i]), xy=(x,y), horizontalalignment='center', verticalalignment='bottom')

ax[1].plot(df['time'], df['velocity'])
ax[1].scatter(df['time'][df['Outlierfiltered']], df['velocity'][df['Outlierfiltered']],color ='r')

f.suptitle(ds.filename)
ax[0].set_title('eye gaze with linear regression and r squared values')
ax[1].set_title('velocity with outliers. outlier threshold = {0}'.format(outlier_threshold))
plt.show()

# # histogram
# hist, bins = np.histogram(np.power(r_value_array,2))
# width = 0.7 * (bins[1] - bins[0])
# center = (bins[:-1] + bins[1:]) / 2
# plt.bar(center, hist, align='center', width=width)
# plt.show()


# Refine linear regression --------------------------------------------------------------------------------------
# If a linear regression fit results in a bad fit (r squared value smaller than 0.3), 
# this segment will be split into several smaller segments.
# Then, there will be computed two linear regressions. 
# One from the start of the segment to the end of the first smaller segment. 
# And the second linear regression from the end of the first smaller segment to the end of the original segment. 
# see animatedfit.gif in trello board.

lr_min_samples = 20  # minimum number of samples to perform the linear regression
fs = 120.0           # sampling frequency of the tobii eyetracker
badfitth = 0.3       # bad fit threshold. a regresison fit with a r_squared value below this, will be refined
numdivisions = 12    # number of divisions to split the bad fits

rf_struct1 = []
rf_struct2 = []


for i in range(n):
    if r_squared_array[i] < badfitth:

        # initialize temporal structs for the linear regression data of the segments of each bad fit
        tmp1 = []
        tmp2 = []

        # get bad fit duration
        bfdur = df['time'][outlier_idx[i+1]] - df['time'][outlier_idx[i]]

        nsamples = bfdur/1000.0 * fs # number of samples in segment

        if nsamples > lr_min_samples:
            for it in range(1, numdivisions):
                s1_start = outlier_idx[i]                                               # segment 1 start
                end = df['time'][s1_start] + it*(bfdur/numdivisions)                         # get the end time of the segment

                val, idx = find_nearest_above(df['time'].values, end)                   # get end's index
                s1_end   = idx

                s2_start = idx                                                          # segment 2 start
                s2_end = outlier_idx[i+1]                                                 # segment 2 end

                # linear regression for segment 1 ------------------------------------------------------------------------------------
                lr_idx = np.arange(s1_start, s1_end)                                     # create linear regression indices array

                # compute linear regression 1
                slope, intercept, r_value, p_value, std_err = stats.linregress(df['time'][lr_idx], df['LEpos_int'][lr_idx])

                # add results to temporal struct
                tmp1.append({'start':df['time'][s1_start], 'end': df['time'][s1_end], 'start_idx': s1_start, 'end_idx':s1_end,
                             'slope':slope, 'intercept': intercept, 'r_value': r_value, 'p_value': p_value, 'std_err': std_err})

                # linear regression for segment 2 ------------------------------------------------------------------------------------
                lr_idx = np.arange(s2_start, s2_end)                                     # create linear regression indices array


                # compute linear regression 2
                slope, intercept, r_value, p_value, std_err = stats.linregress(df['time'][lr_idx], df['LEpos_int'][lr_idx])

                # add results to temporal struct
                tmp2.append({'start':df['time'][s2_start], 'end': df['time'][s2_end], 'start_idx': s1_start, 'end_idx':s1_end,
                             'slope':slope, 'intercept': intercept, 'r_value': r_value, 'p_value': p_value, 'std_err': std_err})

            rf_struct1.append(tmp1)
            rf_struct2.append(tmp2)



# ------------------------------------------------------------------------------------------------------------
# Plot: a) eye gaze with linear regression and r squared values and one refined segment, b) velocity with outliers
HARDCODEDINDEX = 12
f, ax = plt.subplots(2, sharex = True)
ax[0].plot(df['time'], df['LEpos_int'])

for i in range(n):
    
    ax[0].plot(df['time'][outlier_idx[i:i+2]], slope_array[i]*df['time'][outlier_idx[i:i+2]] + intercept_array[i], 'r')
    
    # compute annotation coordinates
    x = df['time'][outlier_idx[i]] + np.diff(df['time'][outlier_idx[i:i+2]])[0]/2.0
    y = np.diff(slope_array[i]*df['time'][outlier_idx[i:i+2]] + intercept_array[i])[0]/2.0
    ax[0].annotate('{0}'.format("%.2f" % r_squared_array[i]), xy=(x,y), horizontalalignment='center', verticalalignment='bottom')

for a in rf_struct1[HARDCODEDINDEX]:
    ax[0].plot([a['end'],a['end']],[np.min(df['LEpos_int']), np.max(df['LEpos_int'])], 'y')
    
    if a['r_value']**2 > -0.7:
        

        axaxis = np.array([a['start'],a['end']])
        ax[0].plot(axaxis, a['slope']*axaxis + a['intercept'], 'y')
    
        # compute annotation coordinates
        x = axaxis[0] + np.diff(axaxis)[0]/2.0
        y = np.diff(a['slope']*axaxis + a['intercept'])[0]/2.0 + 2
        ax[0].annotate('{0}'.format("%.2f" % a['r_value']**2), xy=(x,y), horizontalalignment='center', verticalalignment='bottom')

    
for a in rf_struct2[HARDCODEDINDEX]:
    if a['r_value']**2 > -0.7:
        axaxis = np.array([a['start'],a['end']])
        ax[0].plot(axaxis, a['slope']*axaxis + a['intercept'], 'g')
    
        # compute annotation coordinates
        x = axaxis[0] + np.diff(axaxis)[0]/2.0
        y = np.diff(a['slope']*axaxis + a['intercept'])[0]/2.0 + 2
        ax[0].annotate('{0}'.format("%.2f" % a['r_value']**2), xy=(x,y), horizontalalignment='center', verticalalignment='bottom')
    
ax[1].plot(df['time'], df['velocity'])
ax[1].scatter(df['time'][df['Outlierfiltered']], df['velocity'][df['Outlierfiltered']],color ='r')
ax[1].scatter(df['time'][df['isAmbiguousOutlier']], df['velocity'][df['isAmbiguousOutlier']],color ='y')

f.suptitle(ds.filename)
ax[0].set_title('eye gaze with linear regression and r squared values')
ax[1].set_title('velocity with outliers. outlier threshold = {0}'.format(outlier_threshold))
plt.show()