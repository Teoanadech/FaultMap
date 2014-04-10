# -*- coding: utf-8 -*-
"""
Created on Sun Mar 16 21:00:03 2014

@author: Simon
"""

import json
import os


def ensure_existance(location, make=False):
    if not os.path.exists(location):
        if make:
            os.makedirs(location)
        else:
            raise IOError("File does not exists: {}".format(location))
    return location

def runsetup(mode='test_cases', case='weightcalc_tests'):
    """Gets all required parameters from the case configuration file.

    Mode can be either 'test_cases' or 'plants' as required to get to the
    correct directory.

    """

    if mode == 'test_cases':
        saveloc = 'test_exports'
        casedir = 'test_configs'
        infodynamicsloc = 'infodynamics.jar'

    elif mode == 'plants':

        # Load directories config file
        dirs = json.load(open('config.json'))
        # Get data and preferred export directories from
        # directories config file
        locations = [ensure_existance(os.path.expanduser(dirs[location]))
                     for location in ['dataloc', 'saveloc', 'infodynamicsloc']]
        dataloc, saveloc, infodynamicsloc = locations

        # Define case data directory
        casedir = ensure_existance(os.path.join(dataloc, mode, case), make=True)

    return saveloc, casedir, infodynamicsloc