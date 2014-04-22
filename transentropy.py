"""Module containing functions used in calculation of transfer entropy
Created on Mon Feb 24 15:18:33 2014

@author: Simon Streicher
"""
import numpy as np
import jpype
from sklearn import preprocessing

from jpype import *


def vectorselection(data, timelag, sub_samples, k=1, l=1):
    """Generates sets of vectors from tags time series data
    for calculating transfer entropy.

    For notation references see Shu2013.

    Takes into account the time lag (number of samples between vectors of the
    same variable).

    In this application the prediction horizon (h) is set to equal
    to the time lag.

    The first vector in the data array should be the samples of the variable
    to be predicted (x) while the second vector should be sampled of the vector
    used to make the prediction (y).

    sub_samples is the amount of samples in the dataset used to calculate the
    transfer entropy between two vectors and must satisfy
    sub_samples <= samples

    The required number of samples is extracted from the end of the vector.
    If the vector is longer than the number of samples specified plus the
    desired time lag then the remained of the data will be discarded.

    k refers to the dimension of the historical data to be predicted (x)

    l refers to the dimension of the historical data used
    to do the prediction (y)

    """
    _, sample_n = data.shape
    x_pred = data[0, sample_n-sub_samples:]
    x_pred = x_pred[np.newaxis, :]

    x_hist = np.zeros((k, sub_samples))
    y_hist = np.zeros((l, sub_samples))

    for n in range(1, (k+1)):
        # Original form according to Bauer (2007)
        # TODO: Provide for comparison
        # Modified form according to Shu & Zhao (2013)
        x_hist[n-1, :] = data[1, ((sample_n - sub_samples) - timelag *
                                  (n-1) - 1):(sample_n - timelag * (n-1) - 1)]
    for m in range(1, (l+1)):
        y_hist[m-1:, :] = data[0, ((sample_n - sub_samples) -
                               timelag * (m) - 1):
                               (sample_n - timelag * (m) - 1)]

    return x_pred, x_hist, y_hist


def setup_infodynamics_te():
    """Prepares the teCalc class of the infodynamics toolkit in order to
    calculate transfer entropy according to the kernel method.

    """

    teCalcClass = jpype.JPackage("infodynamics.measures.continuous.kernel") \
                       .TransferEntropyCalculatorKernel
    teCalc = teCalcClass()
    # Normalise the individual variables
    teCalc.setProperty("NORMALISE", "true")

    teCalcClass = None
    del teCalcClass
    jpype.java.lang.System.gc()

    return teCalc


def calc_infodynamics_te(teCalc, affected_data, causal_data):
    """Calculates the transfer entropy for a specific timelag (equal to
    prediction horison) between two sets of time series data.

    This implementation makes use of the infodynamics toolkit:
    https://code.google.com/p/information-dynamics-toolkit/

    sub_samples is the amount of samples in the dataset used to calculate the
    transfer entropy between two vectors (taken from the end of the dataset)
    and must satisfy sub_samples <= samples

    Currently only supports k = 1 and l = 1

    Used to search through a set of timelags in an attempt to identify the
    original delay, as well as to assign a weight to the causal relationship
    between two tags.

    The transfer entropy should have a maximum value when timelag = delay
    used to generate the autoregressive dataset, or will otherwise indicate the
    dead time between data indicating a causal relationship.

    """

    # Normalise data to be safe
    affected_data_norm = preprocessing.scale(affected_data[np.newaxis, :],
                                             axis=1)
    causal_data_norm = preprocessing.scale(causal_data[np.newaxis, :], axis=1)

    # Use history length 1 (Schreiber k=1),
    # kernel width of 0.5 normalised units
    teCalc.initialise(1, 0.5)

    sourceArray = causal_data_norm[0].tolist()
    destArray = affected_data_norm[0].tolist()

    sourceArrayJava = jpype.JArray(jpype.JDouble, 1)(sourceArray)
    destArrayJava = jpype.JArray(jpype.JDouble, 1)(destArray)

    teCalc.setObservations(sourceArrayJava,
                           destArrayJava)

    transentropy = teCalc.computeAverageLocalOfObservations()

    return transentropy
