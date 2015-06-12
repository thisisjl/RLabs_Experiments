import os, sys
lib_path = os.path.abspath(os.path.join('..','_Libraries'))
sys.path.append(lib_path)
from rlabs_libutils import DataStruct, select_data, gentimeseries, gencontinuousoutliers
import pandas as pd
import matplotlib.pyplot as plt
from itertools import izip

# define convert-to-degrees constants
pix = 1280
DPP = 0.03
framerate = 120.0

# select data
path = select_data()
print path

# get raw data
ds = DataStruct(path)
time = pd.Series(ds.timestamps)
leftgazeX = pd.Series(ds.leftgazeX)
df = pd.DataFrame({'time': time, 'LEpos': leftgazeX})

# get rid of -1.1 (NaN's)
mask = df['LEpos'] == -1.1
df['LEpos'].loc[mask] = None

# convert LEpos to degs
df['LEpos'] = df['LEpos'] * pix * DPP

# interpolate eye position
df['LEpos_int'] = df['LEpos'].interpolate()

# compute velocity for interpolated position:
df['velocity'] = df['LEpos_int'].diff() * framerate

# compute outliers (boolean array):
df['isOutlier'] = abs(df['velocity'] - df['velocity'].mean()) > 1.96*df['velocity'].std()

# create two new DataFrames: for outliers and non-outliers:
outliers = df[df['Outlier']].dropna()
nonoutliers = df[~df['Outlier']].dropna()

# compute A or B given outliers
df['A percept'] = [v>0 if o else 0 for v,o in izip(df['velocity'],df['isOutlier'])]
df['B percept'] = [v<0 if o else 0 for v,o in izip(df['velocity'],df['isOutlier'])]

# compute continuous A or B percepts
df['A percept continuous'] = gencontinuousoutliers(df['A percept'],df['B percept'])
df['B percept continuous'] = gencontinuousoutliers(df['B percept'],df['A percept'])

# generate percept time series (button presses)
df['A press'] = gentimeseries(ds.timestamps, ds.A_ts)
df['B press'] = gentimeseries(ds.timestamps, ds.B_ts)


# plot it --------------------------------------------------------------------------------

ax1 = plt.subplot(4, 1, 1)
ax1.plot(df['time'], df['LEpos_int'], label = 'leftgazeX (interpolated)')

ax2 = plt.subplot(4, 1, 2, sharex = ax1)
ax2.scatter(outliers['time'], outliers['velocity'], color = 'r', label='outliers')
ax2.scatter(nonoutliers['time'], nonoutliers['velocity'], color ='g', label='non-outliers') 
# ax2.set_title('Velocity with outliers determined 1.96 * SD')
ax2.set_ylim()
ax2.legend()
plt.xlabel('time (s)')

ax3 = plt.subplot(4, 1, 3,sharex = ax1)
ax3.plot(df['time'], df['A press'], color = 'r',linewidth=2, label = 'A button press')
ax3.plot(df['time'], df['A percept continuous'], color = 'lightsalmon',linewidth=1, label = 'A eye outlier')
ax3.set_ylim([0, 1.05])
ax3.legend()

ax4 = plt.subplot(4, 1, 4, sharex = ax1, sharey = ax3)
ax4.plot(df['time'], df['B press'], color = 'b',linewidth=2, label = 'B button press')
ax4.plot(df['time'], df['B percept continuous'], color = 'lightblue',linewidth=1, label = 'B eye outlier')
ax4.set_ylim([0, 1.05])
ax4.legend()

plt.xlabel('time (s)')
plt.show()