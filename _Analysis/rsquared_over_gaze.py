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