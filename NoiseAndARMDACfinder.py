#=========================================================================================
# NoiseAndARMDACfinder.py ----------------------------------------------------------------
#-----------------------------------------------------------------------------------------
# Author(s): Brendan Regnery, Jared Sturdy, Brian Dorney ---------------------------------
#-----------------------------------------------------------------------------------------


#=========================================================================================
# Effective Gain Calculator --------------------------------------------------------------
#-----------------------------------------------------------------------------------------
# This function calculates the effective gain from the drift voltage using a supplied ----
# TGraph that shows gain vs divider current ----------------------------------------------
#-----------------------------------------------------------------------------------------

def signalChargeVSeffGainCalculator(currentGraph):
    '''
    return's a list of the effect Gain given a list of drift voltages and a gain vs 
    divider current graph

    voltList - List of drift voltages
    currentGraph - TGraph of effective gain vs divider current
    '''

    # Get necessary modules
    import ROOT as root
    import numpy as np

    # Voltage list And MPV Charge from Vallary's MPV graphs
    # https://cds.cern.ch/record/2298721/
    voltList = [3000, 3050, 3100, 3150, 3200, 3250, 3300, 3350, 3400]
    uniStripChargeMPV = []
    diStripChargeMPV = []
    triStripChargeMPV = []
    quadStripChargeMPV = []
    # Maybe include larger?

    # Calculate divider current using ohm's law
    resist = 5000000
    currentList = [volt / resist for volt in voltList]
    
    # Get current and gain values on the input graph
    currentVal = currentGraph.GetX()
    gainVal = currentGraph.GetY()

    currentVal = np.array(currentVal)
    gainVal = np.array(gainVal)
     
    # Use numpy to fit this to an exponential and find the gain
    funcParam = np.polyfit(currentVal, np.log(gainVal), 1)
    gainList = [np.exp(funcParam[0]) * np.exp(funcParam[1] * current) for current in currentList]

    # Make a TGraph with the MPVs vs effective gain
    # return this TGraph 
