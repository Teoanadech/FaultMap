# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

from scipy import stats
import numpy as np
from numpy import vstack

# <codecell>

def autogen(samples, delay):
    """Generate an autoregressive set of vectors."""

    source = np.random.randn(samples + delay + 1)
    pred = np.zeros_like(source)
    pred_random_add = np.random.rand(samples + delay + 1)

    for i in range(delay, len(source)):
        pred[i] = pred[i - 1] + source[i - delay]

    pred = pred[delay:-1]
    source = source[delay:-1]
    
    pred = pred + pred_random_add[delay:-1]

    data = vstack([pred, source])

    return data

# <codecell>

def vectorselection(data, timelag, sub_samples, k=1, l=1):
    """Generates sets of vectors for calculating transfer entropy.

    For notation references see Shu2013.

    Takes into account the time lag (number of samples between vectors of the
    same variable).

    In this application the prediction horizon (h) is set to equal
    to the time lag.

    The first vector in the data array should be the samples of the variable
    to be predicted (x) while the second vector should be sampled of the vector
    used to make the prediction (y).

    sub_samples is the amount of samples in the dataset used to calculate the
    transfer entropy between two vectors.
    The required number of samples is extracted from the end of the vector.
    If the vector is longer than the number of samples specified plus the
    desired time lag then the remained of the data will be discarded.
    sub_samples <= samples


    k refers to the dimension of the historical data to be predicted (x)

    l refers to the dimension of the historical data used
    to do the prediction (y)

    """
    _, sample_n = data.shape
    x_pred = data[0, sample_n-sub_samples-1:-1]

    x_hist = np.zeros((k, sub_samples))
    y_hist = np.zeros((l, sub_samples))

    for n in range(1, (k+1)):
        # Original form according to Bauer (2007)
#        x_hist[n-1, :] = data[0, ((sample_n - samples) - timelag * n):
#                               (sample_n - timelag * n)]
        # Modified form according to Shu & Zhao (2013)
    # There was big blunders here!!
    # Be careful of not destroying the intent by selecting vectors wrong!!
        x_hist[n-1, :] = data[0, ((sample_n - sub_samples) - timelag *
                                  (n-1) - 2):(sample_n - timelag * (n-1) - 2)]
    for m in range(1, (l+1)):
        y_hist[m-1:, :] = data[1, ((sample_n - sub_samples) - timelag * (m) - 1):
                               (sample_n - timelag * (m) - 1)]

#    for n in range(1, (k+1)):
#        x_hist = data[0, ((sample_n - samples) - timelag * n):
#                            (sample_n - timelag * n)]
#    for m in range(1, (l+1)):
#        y_hist = data[1, ((sample_n - samples) - timelag * m):
#                            (sample_n - timelag * m)]

    return x_pred, x_hist, y_hist

# <codecell>

def pdfcalcs(x_pred, x_hist, y_hist):
    """Calculates the PDFs required to calculate transfer entropy.

    Currently only supports k = 1; l = 1

    """
    # TODO: Generalize for k and l

    # Get dimensions of vectors
#    k = np.size(x_hist[:, 1])
#    l = np.size(y_hist[:, 1])

    # Calculate p(x_{i+h}, x_i, y_i)
    data_1 = np.vstack([x_pred, x_hist[0, :], y_hist[0, :]])
    pdf_1 = stats.gaussian_kde(data_1, 'silverman')

    # Calculate p(x_i, y_i)
    data_2 = np.vstack([x_hist[0, :], y_hist[0, :]])
    pdf_2 = stats.gaussian_kde(data_2, 'silverman')

    # Calculate p(x_{i+h}, x_i)
    data_3 = np.vstack([x_pred, x_hist[0, :]])
    pdf_3 = stats.gaussian_kde(data_3, 'silverman')

    # Calculate p(x_i)
    data_4 = x_hist[0, :]
    pdf_4 = stats.gaussian_kde(data_4, 'silverman')

    return pdf_1, pdf_2, pdf_3, pdf_4

# <codecell>

def te_elementcalc(pdf_1, pdf_2, pdf_3, pdf_4, x_pred_val,
                   x_hist_val, y_hist_val):
    """Calculate elements for summation for a specific set of coordinates"""

    # Need to find a proper way to correct for cases when PDFs return 0
    # Most of the PDF issues are associated with the x_hist values being
    # very similar to the x_pred values
    # Some very small negative values are sometimes returned

    # Function evaluations
    term1 = pdf_1([x_pred_val, x_hist_val, y_hist_val])
    term2 = pdf_2([x_hist_val, y_hist_val])
    term3 = pdf_3([x_pred_val, x_hist_val])
    term4 = pdf_4([x_hist_val])
#    print term1, term2, term3, term4

    # Assign zero value if nan is returned

#    print term1, term2, term3, term4
#    if term1 == 0 or term2 == 0 or term3 == 0 or term4 == 0:
#        sum_element = 0
#        print term1, term2, term3, term4
#
#    else:
#        logterm_num = (term1 / term2)
#        logterm_den = (term3 / term4)
#        coeff = term1
#        sum_element = coeff * np.log(logterm_num / logterm_den)
#        print np.log(logterm_num / logterm_den)

    logterm_num = (term1 / term2)
    logterm_den = (term3 / term4)
    coeff = term1
    sum_element = coeff * np.log(logterm_num / logterm_den)
    
    #print sum_element

    if str(sum_element[0]) == 'nan':
        sum_element = 0
        
    #print sum_element

    return sum_element

# <codecell>

def te_calc(x_pred, x_hist, y_hist, ampbins):
    """Calculates the transfer entropy between two variables from a set of
    vectors already calculated.

    ampbins is the number of amplitude bins to use over each variable

    """

    # First do an example for the case of k = l = 1
    # TODO: Sum loops to allow for a general case

    # Divide the range of each variable into amplitude bins to sum over

    x_pred_min = x_pred.min()
    x_pred_max = x_pred.max()
    x_hist_min = x_hist.min()
    x_hist_max = x_hist.max()
    y_hist_min = y_hist.min()
    y_hist_max = y_hist.max()

    x_pred_space = np.linspace(x_pred_min, x_pred_max, ampbins)
    x_hist_space = np.linspace(x_hist_min, x_hist_max, ampbins)
    y_hist_space = np.linspace(y_hist_min, y_hist_max, ampbins)

    x_pred_diff = x_pred_space[1] - x_pred_space[0]
    x_hist_diff = x_hist_space[1] - x_hist_space[0]
    y_hist_diff = y_hist_space[1] - y_hist_space[0]

    # Calculate PDFs for all combinations required
    [pdf_1, pdf_2, pdf_3, pdf_4] = pdfcalcs(x_pred, x_hist, y_hist)

    # Consecutive sums
    # TODO: Make sure Riemann sum diff elements is handled correctly

    tesum = 0
#    tesum_old = -1
#    sumelement_store = np.zeros(ampbins**3)
    delement = x_pred_diff * x_hist_diff * y_hist_diff
    #print 'delement', delement
    counter = 0
    runs = len(x_pred_space)
    #print 'starting...'
    for s1 in x_pred_space:
        counter = counter + 1.0
        #print (counter / runs) * 100, '%'
        for s2 in x_hist_space:
#            print 's2', s2
            for s3 in y_hist_space:
#                print 's3', s3
                sumelement = te_elementcalc(pdf_1, pdf_2, pdf_3, pdf_4,
                                             s1, s2, s3)
                tesum = tesum + sumelement
                # Try to detect point at which the huge term enters
                # For special case of data = np.vstack([puretf, original])
                # and timelag = 1 and ampbins = 20
                # Has to do with a huge value for PDF1 at a specific point
#                if tesum / tesum_old < 0:
#                    print s1, s2, s3
#                    temp1 = pdf_1([s1, s2, s3])
#                    temp2 = pdf_2([s2, s3])
#                    temp3 = pdf_3([s1, s2])
#                    temp4 = pdf_4([s2])
#                    print temp1, temp2, temp3, temp4
#                tesum_old = tesum
#                print tesum
#                sumelement_store[s1*s2*s3] = sumelement
        
    tentropy = tesum * delement

    # Using local sums
    # (It does give the same result)

#    sums3 = 0
#    sums2 = 0
#    sums1 = 0
#    for s1 in x_pred_space:
#        print s1
#        sums2 = 0
#        for s2 in x_hist_space:
##            print s2
#            sums3 = 0
#            for s3 in y_hist_space:
#                sum_element = tecalc(pdf_1, pdf_2, pdf_3, pdf_4, s1, s2, s3)
#                sums3 = sums3 + sum_element
#            sums2 = sums2 + sums3 * y_hist_diff
#        sums1 = sums1 + sums2 * x_hist_diff
#        te = sums1 * x_pred_diff

    return tentropy

# <codecell>

def getdata(samples, delay):
    """Get dataset for testing.

    Select to generate each run or import an existing dataset.

    """

    # Generate autoregressive delayed data vectors internally
    data = autogen(samples, delay)

    # Alternatively, import data from file
#    autoregx = loadtxt('autoregx_data.csv')
#    autoregy = loadtxt('autoregy_data.csv')

    return data

# <codecell>

def calculate_te(delay, timelag, samples, sub_samples, ampbins, k=1, l=1):
    """Calculates the transfer entropy for a specific timelag (equal to
    prediction horison) for a set of autoregressive data.

    sub_samples is the amount of samples in the dataset used to calculate the
    transfer entropy between two vectors (taken from the end of the dataset).
    sub_samples <= samples

    Currently only supports k = 1; l = 1;

    You can search through a set of timelags in an attempt to identify the
    original delay.
    The transfer entropy should have a maximum value when timelag = delay
    used to generate the autoregressive dataset.

    """
    # Get autoregressive datasets
    data = getdata(samples, delay)

    [x_pred, x_hist, y_hist] = vectorselection(data, timelag,
                                               sub_samples, k, l)

    transentropy = te_calc(x_pred, x_hist, y_hist, ampbins)

    return transentropy

# <codecell>

# Calculate transfer entropy
# Delay = 4
delay = 4
DATA = getdata(1000, delay)

# <codecell>

# Timelag = 1
[X_PRED_1, X_HIST_1, Y_HIST_1] = vectorselection(DATA, 1, 100)
# Timelag = 2
[X_PRED_2, X_HIST_2, Y_HIST_2] = vectorselection(DATA, 2, 100)
# Timelag = 3
[X_PRED_3, X_HIST_3, Y_HIST_3] = vectorselection(DATA, 3, 100)
# Timelag = 4
[X_PRED_4, X_HIST_4, Y_HIST_4] = vectorselection(DATA, 4, 100)
# Timelag = 5
[X_PRED_5, X_HIST_5, Y_HIST_5] = vectorselection(DATA, 5, 100)
# Timelag = 6
[X_PRED_6, X_HIST_6, Y_HIST_6] = vectorselection(DATA, 6, 100)
# Timelag = 7
[X_PRED_7, X_HIST_7, Y_HIST_7] = vectorselection(DATA, 7, 100)
# Timelag = 8
[X_PRED_8, X_HIST_8, Y_HIST_8] = vectorselection(DATA, 8, 100)
# Timelag = 9
[X_PRED_9, X_HIST_9, Y_HIST_9] = vectorselection(DATA, 9, 100)
# Timelag = 10
[X_PRED_10, X_HIST_10, Y_HIST_10] = vectorselection(DATA, 10, 100)

# <codecell>

TRANSENTROPY_1 = te_calc(X_PRED_1, X_HIST_1, Y_HIST_1, 30)
TRANSENTROPY_2 = te_calc(X_PRED_2, X_HIST_2, Y_HIST_2, 30)
TRANSENTROPY_3 = te_calc(X_PRED_3, X_HIST_3, Y_HIST_3, 30)
TRANSENTROPY_4 = te_calc(X_PRED_4, X_HIST_4, Y_HIST_4, 30)
TRANSENTROPY_5 = te_calc(X_PRED_5, X_HIST_5, Y_HIST_5, 30)
TRANSENTROPY_6 = te_calc(X_PRED_6, X_HIST_6, Y_HIST_6, 30)
TRANSENTROPY_7 = te_calc(X_PRED_7, X_HIST_7, Y_HIST_7, 30)
TRANSENTROPY_8 = te_calc(X_PRED_8, X_HIST_8, Y_HIST_8, 30)
TRANSENTROPY_9 = te_calc(X_PRED_9, X_HIST_9, Y_HIST_9, 30)
TRANSENTROPY_10 = te_calc(X_PRED_10, X_HIST_10, Y_HIST_10, 30)

# <codecell>

ENTROPIES = [TRANSENTROPY_1, TRANSENTROPY_2, TRANSENTROPY_3, TRANSENTROPY_4, TRANSENTROPY_5, TRANSENTROPY_6,
             TRANSENTROPY_7, TRANSENTROPY_8, TRANSENTROPY_9, TRANSENTROPY_10]
ENTROPIES

# <codecell>

ENTROPIES[delay-1]

# <codecell>

max(ENTROPIES)

# <codecell>


# <codecell>

#import unittest
#assertEqual(ENTROPIES[delay-1], max(ENTROPIES))

# <codecell>

# It appears as if this can't be handled due to the very close covariance
# Let's attempt to break the close covariance by introducing another small random element

# <codecell>

