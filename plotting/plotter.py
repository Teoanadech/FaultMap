# -*- coding: utf-8 -*-
"""
@author: Simon

This module executes all functions needed to draw desired plots.


"""
import os
import json
import logging

import figtypes
from ranking import data_processing

import config_setup


class GraphData(object):
    """Creates a graph object storing information required by
    graphing functions.

    """

    def __init__(self, mode, case):

        # Get locations from configuration file
        self.saveloc, self.caseconfigloc, self.casedir, _ = \
            config_setup.runsetup(mode, case)
        self.mode = mode
        self.case = case

        # Load case config file
        self.caseconfig = json.load(
            open(os.path.join(self.caseconfigloc, case +
                              '_plotting' + '.json')))

        # Load weight case config file
        # This is used in plots that make use of original time series data
        self.weight_caseconfig = json.load(
            open(os.path.join(self.caseconfigloc, case +
                              '_weightcalc' + '.json')))

        # Get graphs
        self.graphs = self.caseconfig['graphs']
        # Get weight_methods
        self.weight_methods = self.caseconfig['weight_methods']
        # Get data type
        self.datatype = self.caseconfig['datatype']

    def graphdetails(self, graph):
        """Retrieves data particular for each graph that is to be drawn.

        """
        self.plot_type = self.caseconfig[graph]['plot_type']
        self.scenarios = self.caseconfig[graph]['scenarios']
        self.axis_limits = self.caseconfig[graph]['axis_limits']
        self.weight_methods = self.caseconfig[graph]['weight_methods']

    def get_plotvars(self, graph):
        self.plotvars = self.caseconfig[graph]['plotvars']

    def get_sourcevars(self, graph):
        self.sourcevars = self.caseconfig[graph]['sourcevars']

    def get_destvars(self, graph):
        self.destvars = self.caseconfig[graph]['destvars']

    def get_boxindexes(self, graph):
        self.boxindexes = self.caseconfig[graph]['boxindexes']

    def get_xvalues(self, graph):
        self.xvals = self.caseconfig[graph][graph]['xvals']

    def get_legendbbox(self, graph):
        self.legendbbox = self.caseconfig[graph]['legendbbox']

    def get_linelabels(self, graph):
        self.linelabels = self.caseconfig[graph]['linelabels']

    def get_labelformat(self, graph):
        self.labelformat = self.caseconfig[graph]['labelformat']

    def get_starttime(self, graph):
        self.starttime = self.caseconfig[graph]['starttime']

    def get_frequencyunit(self, graph):
        self.frequencyunit = self.caseconfig[graph]['frequency_unit']

    def get_timeunit(self, graph):
        self.timeunit = self.caseconfig[graph]['time_unit']

    def get_sigthresholdplotting(self, graph):
        self.thresholdplotting = self.caseconfig[graph]['threshold_plotting']

    def get_varindexes(self, graph):
        self.varindexes = [x+1 for x in
                           self.caseconfig[graph]['varindexes']]


def get_scenario_data_vectors(graphdata):
    """Extract value matrices from different scenarios."""

    valuematrices = []

    for scenario in graphdata.scenario:
        sourcefile = filename_template.format(
            graphdata.case, scenario,
            graphdata.method[0], graphdata.sigstatus, graphdata.boxindex,
            graphdata.sourcevar)
        valuematrix, _ = \
            data_processing.read_header_values_datafile(sourcefile)
        valuematrices.append(valuematrix)

    return valuematrices


def get_box_data_vectors(graphdata):
    """Extract value matrices from different boxes and different
    source variables.

    Returns a list of list, with entries in the first list referring to
    a specific box, and entries in the second list referring to a specific
    source variable.

    """

    valuematrices = []
    # Get number of source variables
    for box in graphdata.boxindex:
        sourcevalues = []
        for sourceindex, sourcevar in enumerate(graphdata.sourcevar):
            sourcefile = filename_template.format(
                graphdata.case, graphdata.scenario,
                graphdata.method[0], graphdata.sigstatus, box,
                sourcevar)
            valuematrix, _ = \
                data_processing.read_header_values_datafile(sourcefile)
            sourcevalues.append(valuematrix)
        valuematrices.append(sourcevalues)

    return valuematrices


def get_box_ranking_scores(graphdata):
    """Extract rankings scores for different variables over a range of boxes.

    Makes use of the boxrankdict as input.

    Returns a list of list, with entries in the first list referring to
    a specific node, and entries in the second list referring to a specific
    box.

    """

    importancedict_filename = importancedict_filename_template.format(
        graphdata.case, graphdata.scenario,
        graphdata.method[0])

    boxrankdict = json.load(open(importancedict_filename))
    importancelist = boxrankdict.items()

    return importancelist


def get_box_threshold_vectors(graphdata):
    """Extract significance threshold matrices from different boxes and different
    source variables.

    Returns a list of list, with entries in the first list referring to
    a specific box, and entries in the second list referring to a specific
    source variable.

    """

    valuematrices = []
    # Get number of source variables
    for box in graphdata.boxindex:
        sourcevalues = []
        for sourceindex, sourcevar in enumerate(graphdata.sourcevar):
            sourcefile = filename_sig_template.format(
                graphdata.case, graphdata.scenario,
                graphdata.method[0], box,
                sourcevar)
            valuematrix, _ = \
                data_processing.read_header_values_datafile(sourcefile)
            sourcevalues.append(valuematrix)
        valuematrices.append(sourcevalues)

    return valuematrices


def drawplot(graphdata, scenario, datadir, graph, writeoutput):

    dirparts = data_processing.getfolders(datadir)
    dirparts[dirparts.index('weightdata')] = 'graphs'
    savedir = dirparts[0]
    for pathpart in dirparts[1:]:
        savedir = os.path.join(savedir, pathpart)

    if os.path.exists(os.path.join(savedir, '{}.pdf'.format(graph))):
        logging.info("The requested graph has already been drawn")
    elif writeoutput:
        config_setup.ensure_existence(os.path.join(savedir))
        eval('figtypes.' + graphdata.plot_type)(
            graphdata, graph, scenario, savedir)

    return None


def plotdraw(mode, case, writeoutput):

    graphdata = GraphData(mode, case)

    # Create output directory
    config_setup.ensure_existence(
        os.path.join(graphdata.saveloc,
                     'graphs'), make=True)

    for graph in graphdata.graphs:
        graphdata.graphdetails(graph)
        for weight_method in graphdata.weight_methods:
            print weight_method
            for scenario in graphdata.scenarios:
                print scenario
                basedir = os.path.join(graphdata.saveloc, 'weightdata',
                                       case, scenario, weight_method)

                sigtypes = next(os.walk(basedir))[1]

                for sigtype in sigtypes:
                    print sigtype
                    embedtypesdir = os.path.join(basedir, sigtype)
                    embedtypes = next(os.walk(embedtypesdir))[1]
                    for embedtype in embedtypes:
                        print embedtype
                        datadir = os.path.join(embedtypesdir, embedtype)
                        # Actual plot drawing execution starts here
                        drawplot(graphdata, scenario, datadir,
                                 graph, writeoutput)

    return None