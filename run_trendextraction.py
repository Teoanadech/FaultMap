"""
Calculates and writes trends for different weight types and delays
from data generated by run_createarrays process.

@author: Simon Streicher
"""
import logging
import json
import os

import config_setup
from ranking.data_processing import trend_extraction

logging.basicConfig(level=logging.INFO)

dataloc, configloc, saveloc = config_setup.get_locations()
trendextraction_config = json.load(open(
    os.path.join(configloc, 'config_trendextraction' + '.json')))

writeoutput = trendextraction_config['writeoutput']
mode = trendextraction_config['mode']
cases = trendextraction_config['cases']

for case in cases:
    trend_extraction(mode, case, writeoutput)