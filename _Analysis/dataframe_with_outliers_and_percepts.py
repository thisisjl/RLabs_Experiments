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

# compute outliers (boolean array)
df['Outlier'] = abs(df['velocity'] - df['velocity'].mean()) > 1.96*df['velocity'].std()

# compute A or B given outliers
df['A percept'] = [v>0 if o else 0 for v,o in izip(df['velocity'],df['Outlier'])]
df['B percept'] = [v<0 if o else 0 for v,o in izip(df['velocity'],df['Outlier'])]

# compute continuous A or B percepts
df['A percept continuous'] = gencontinuousoutliers(df['A percept'],df['B percept'])
df['B percept continuous'] = gencontinuousoutliers(df['B percept'],df['A percept'])

# generate percept time series (button presses)
df['A press'] = gentimeseries(ds.timestamps, ds.A_ts)
df['B press'] = gentimeseries(ds.timestamps, ds.B_ts)

# plot it
showlegend = 1

ax1 = plt.subplot(3, 1, 1)
ax1.plot(df['time'], df['LEpos_int'], label = 'leftgazeX (interpolated)')

plt.title('')
plt.ylabel('')

ax2 = plt.subplot(3, 1, 2,sharex = ax1)
ax2.plot(df['time'], df['A press'], color = 'r',linewidth=2, label = 'A button press')
ax2.plot(df['time'], df['A percept continuous'], color = 'lightsalmon',linewidth=1, label = 'A eye outlier')
plt.ylim(ymax = 1.05)

ax3 = plt.subplot(3, 1, 3, sharex = ax1, sharey = ax2)
ax3.plot(df['time'], df['B press'], color = 'b',linewidth=2, label = 'B button press')
ax3.plot(df['time'], df['B percept continuous'], color = 'lightblue',linewidth=1, label = 'B eye outlier')

if showlegend:
	ax1.legend(loc='upper right')
	ax2.legend(loc='upper right')
	ax3.legend(loc='upper right')
plt.ylim(ymax = 1.05)

plt.xlabel('time (s)')
plt.show()