import os, sys
lib_path = os.path.abspath(os.path.join('..','_Libraries'))
sys.path.append(lib_path)
from rlabs_libutils import DataStruct, select_data, create_outlier_df
from rlabs_liblinreg import * 																# new library for the linear regression functions
import matplotlib.pyplot as plt
import numpy as np

# Read raw data -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  
path = select_data()
ds = DataStruct(path)

# Create outlier data frame -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  
outlier_threshold = 100  # velocity values over 100 will be outliers.
ambiguousoutlier_th = 80 # velocity values between 80 and 100 will be ambiguous outliers.
filter_samples = 5       # the samples following an outlier will not be outliers.

df = create_outlier_df(ds,outlier_threshold = outlier_threshold, 
                      ambiguousoutlier_th = ambiguousoutlier_th, filter_samples = filter_samples)

# Compute linear regression  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  
outlier_idx = np.where(df['Outlierfiltered'])[0]   											# indexes where are outliers
amb_outlier_idx = np.where(df['isAmbiguousOutlier'])[0] 									# idexes where are ambiguous outliers
n = len(outlier_idx)-1 																		# number of outliers
lr_struct = [] 																				# initialize linear regression list (will be populates with dicts)

print '\ncomputing linear regression'
for i in range(n): 																			# for each outlier

	fit = regressionbtwpoints(df, outlier_idx[i], outlier_idx[i+1]) 						# compute the linear regression between an outlier and the next outlier
	fit = refineregression(fit, df, minintervallen = 30, thresrsq = 0.3) 					# refine fit (will output fit if refinement not necessary)

	if type(fit) is list: 																	# if refinement outputs more than one segment
		for f in fit: 																		# get each segment 
			lr_struct.append(f) 															# and put it in array
	else: 																					# if only one segment (not refined)
		lr_struct.append(fit) 																# put it in array
	
	# write progress in terminal
	sys.stdout.write('\r{0} of {1}'.format(i,n-1))
	sys.stdout.flush()


# Plotting  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  
print '\nplotting'
f, ax = plt.subplots(1, sharex = True,sharey = True)

ax.plot(df['time'], df['LEpos_int'])
ax.scatter(df['time'][df['Outlierfiltered']], df['LEpos_int'][df['Outlierfiltered']],color ='r')
ax.scatter(df['time'][df['isAmbiguousOutlier']], df['LEpos_int'][df['isAmbiguousOutlier']],color ='y')

for a in lr_struct:
	axaxis = np.array([a['start'],a['end']])
	ax.plot(axaxis, a['slope']*axaxis + a['intercept'], 'r')


	# compute annotation coordinates
	x = axaxis[0] + np.diff(axaxis)[0]/2.0
	y = np.diff(a['slope']*axaxis + a['intercept'])[0]/2.0# + 2
	ax.annotate('{0}'.format(a['percept']),xy=(x,y), horizontalalignment='center', verticalalignment='bottom')   

	# ax.annotate('{4}\n{5}\nr^2: {0}\nRSS: {1}\nslp: {2}\n{3}'.format(
		#                 "%.2f" % a['r_value']**2,"%.2f" % a['RSS'], "%.4f" % a['slope'], a['percept'],a['end_idx']-a['start_idx'],i),
		#                        xy=(x,y), horizontalalignment='center', verticalalignment='bottom')   

f.suptitle(ds.filename)
ax.set_title('eye gaze with linear regression')

plt.show()