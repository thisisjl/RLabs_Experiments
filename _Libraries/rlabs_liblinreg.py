import numpy as np
from scipy import stats

def regressionbtwpoints(df, start, end, xlabel = 'time', ylabel = 'LEpos_int'):
    """
        Compute the linear regression of df between start and end points.
        
        Input:
        - df: Pandas.DataFrame containing eyetracker data
        - start: starting point for the linear regression
        - end: ending point for the linear regression
        - xlabel: df data to use as horizontal axis of the linear regression. Default as 'time'
        - ylabel: df data to use as vertical axis of the linear regression. Default as 'LEpos_int'

        Output:
        - tmp: dictionary containing linear regression results
        
        References:
        - http://modelling3e4.connectmv.com/wiki/Software_tutorial/Least_squares_modelling_(linear_regression)

    """
    lr_idx = np.arange(start, end)                                                                                  # indices array
    n = len(lr_idx)
    x = df[xlabel][lr_idx]
    y = df[ylabel][lr_idx]

    # compute linear regression:
    slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
    
    # additional calculations:
    r_squared = r_value**2
    resids = y - np.dot(np.vstack([np.ones(n), x]).T, [intercept, slope])       # e = y - Xa; 
    RSS = sum(resids**2) # residual sum of squares
    TSS = sum((y - np.mean(y))**2) # total sum of squares
    R2 = 1 - RSS/TSS
    std_y = np.sqrt(TSS/(n-1)) 

    # add results to temporal struct:
    tmp = {'start':df['time'][start], 'end': df['time'][end], 'start_idx': start, 'end_idx':end,
                 'slope':slope, 'intercept': intercept, 'r_value': r_value, 'p_value': p_value, 'std_err': std_err,
           'r_squared': r_squared, 'resids': resids, 'RSS': RSS, 'TSS': TSS, 'R2': R2, 'std_y': std_y}

    return tmp

# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 

def method1_useamboutls(df, itvl_start, itvl_end, btwpoints):
    """
        Refinement method 1: Using ambiguous outliers.

        Input:
        - df: data frame
        - itvl_start: interval start (first outlier)
        - itvl_end: interval end (second outlier)
        - btwpoints: samples between points (threshold)
        
        Output:
        - m1_struct: list of dictionaries containing the regression data.
    """

    # get the indices of the ambiguous outliers in the interval
    amb_outlier_idx = np.where(df['isAmbiguousOutlier'])[0]
    amb_btwn_outlrs = amb_outlier_idx[(np.where((amb_outlier_idx >= itvl_start+btwpoints) & (amb_outlier_idx <= itvl_end-btwpoints)))]
    
    # get the ambiguous outliers that are separated by btwpoints samples
    nwlridx = [amb_btwn_outlrs[0]] # always use first ambiguous outlier
    for item in amb_btwn_outlrs: # for all the points
        if item > (nwlridx[-1]+btwpoints): # if point is greater than last point in nwlridx,
            nwlridx.append(item) # get it
    nwlridx.insert(0,itvl_start)                    # prepend interval start
    nwlridx.insert(len(nwlridx),itvl_end)           # append interval end
    
    m1_struct = []                                  # define struct with regression data

    for j in range(len(nwlridx)-1):                         # for all the points
        sgm_start = nwlridx[j]                              # get the segment start
        sgm_end = nwlridx[j+1]                              # get the segment end
        tmp = regressionbtwpoints(df, sgm_start, sgm_end)   # compute linear regression
        m1_struct.append(tmp)                               # append results to struct
        
    return m1_struct

# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 

def method2_splitintrvl(df, itvl_start, itvl_end, maxdivisions, minsamples, fs = 120.0):
    """
        Refinement method 2: split interval in segments

        Input:
        - df: data frame
        - itvl_start: interval start (first outlier)
        - itvl_end: interval end (second outlier)
        - maxdivisions: maximum number of divisions allowed
        - minsamples: minimum number of samples in a segment
        - fs: sampling frequency of the data (120 Hz for Tobii X120)

        Output:
        - m2_struct1: list of dictionaries containing the regression data of the left segments.
        - m2_struct2: list of dictionaries containing the regression data of the right segments.
    """

    bfdur = df['time'][itvl_end] - df['time'][itvl_start]                   # get bad fit duration

    nsamples = bfdur/1000.0 * fs                                            # number of samples in segment

    while (nsamples / maxdivisions) < minsamples:                           # if shortest segment is shorter than minsamples, 
        maxdivisions -= 1                                                   # decrease number of divisions
    
    m2_struct1 = []                                                         # define struct that will contain regression data
    m2_struct2 = []                                                         # define struct that will contain regression data
    for it in range(1, maxdivisions):
        
        # segment 1 -----------------------------------------------------------------------------------------------------------
        # start and end indices segment 1
        s1_start = itvl_start                                               # segment 1 always starts where interval starts
        end   = df['time'][s1_start] + it * (bfdur / maxdivisions)          # end of segment 1 in seconds
        _, s1_end = find_nearest_above(df['time'].values, end)              # index of the end of segment 1

        tmp1 = regressionbtwpoints(df, s1_start, s1_end)                    # compute linear regression

        # segment 2 ----------------------------------------------------------------------------------------------------------
        # start and end indices segment 1
        s2_start = s1_end
        s2_end = itvl_end

        tmp2 = regressionbtwpoints(df, s2_start, s2_end)                        # compute linear regression
        
        # append to structs
        m2_struct1.append(tmp1)
        m2_struct2.append(tmp2)

    # get best fit index
    bestfit = getbestjointfit(m2_struct1, m2_struct2)


    return m2_struct1, m2_struct2, bestfit

# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 

def getbestjointfit(segm1, segm2):
    """
        Sum the r squared value of each corresponding segment
        and return the index of the maximum.
        
        Input:
            - segm1, segm2: element of refined linear regression struct. (not rf_struct1, but rf_struct[i])
        Output:
            - max_idx: the index where the refinement segments have the greater joint r squared value.
    """
    
    r_squared1 = np.power(np.array([item['r_value'] for item in segm1]),2)
    r_squared2 = np.power(np.array([item['r_value'] for item in segm2]),2)

    joint_rsquared = r_squared1 + r_squared2
    max_idx = np.where(joint_rsquared == np.max(joint_rsquared))[0]
   
    return max_idx