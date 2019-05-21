#!/bin/env python

r"""
``plotSbitThreshComp.py`` - compares sbit threshold measurements
================================================================

Synopsis
--------

**plotSbitThreshComp.py** [*OPTIONS*]

Description
-----------

This script reads in a list of scandate file, see :func:`gempython.gemplotting.utils.anautilities.parseListOfScanDatesFile` for details, and for each scandate the set of sbit vs. CFG_THR_ARM_DAC plots (generated by :program:`gempython.vfatqc.sbitThreshScanParallel.py` or :program:`gempython.vfatqc.sbitThreshScanSeries.py`, for each VFAT position, will be plotted on a common 3x8 grid canvas.  A TLegend will automatically be plotted and the legend entry will be taken from the third column of the input list of scandates files.

Arguments
---------

Mandatory arguments
...................

The following list shows the mandatory inputs that must be supplied to execute
the script:

.. program:: plotSbitThreshComp.py

.. option:: filename <FILE>

    Physical filename of the input file to be passed to :program:`plot_eff.py`.
    The format of this input file should follow the :doc:`Three Column Format
    </scandate-list-formats>`.

Optional arguments
..................

The following list shows the optional inputs that can be supplied when
executing the script:

.. option:: -a,--alphaLabels

    Provide this argument if alphanumeric characters exist in the third column of :option:`filename`.

.. option:: -c,--calFileARM 

    File specifying CFG_THR_ARM_DAC calibration per vfat.  If provided x-axis of each VFAT will be converted from DAC units to charge units (fC).  Format of file follows from TTree::ReadFile() with branch names: 'vfatN/I:coef4/F:coef3/F:coef2/F:coef1/F:coef0/F'

.. option:: -n,--noLeg

    If provided, do not draw a TLegend on the output plots

.. option:: -s --savePlots

   Make *.png file for all plots that will be saved in the output TFile 

Example
-------

.. code-block:: bash

    plotSbitThreshComp.py -a -c calFieArm.txt --savePlots inputListOfScanDates.txt 

"""

def compareSBitThreshResults(args):
    # Suppress all pop-ups from ROOT
    import ROOT as r
    r.gROOT.SetBatch(True)
    
    # Check Paths
    import os
    from gempython.utils.wrappers import envCheck
    envCheck('DATA_PATH')
    envCheck('ELOG_PATH')
    elogPath = os.getenv('ELOG_PATH')

    # Get info from input file
    from gempython.gemplotting.utils.anautilities import getCyclicColor, getDirByAnaType, filePathExists, make3x8Canvas, parseArmDacCalFile, parseListOfScanDatesFile
    parsedTuple = parseListOfScanDatesFile(args.filename,alphaLabels=args.alphaLabels)
    listChamberAndScanDate = parsedTuple[0]
    chamberName = listChamberAndScanDate[0][0]
    thrDacName = parsedTuple[1]

    # Parse calibration file if present
    arrayCalInfo = None 
    if args.calFileARM is not None:
        arrayCalInfo = parseArmDacCalFile(args.calFileARM) # arrayCalInfo[i][vfatN] for coef of x^(4-i)

    legPlot = r.TLegend(0.5,0.5,0.9,0.9)
    
    from array import array
    from gempython.utils.nesteddict import nesteddict as ndict
    dict_Histos = ndict()
    dict_Graphs = ndict()
    dict_MultiGraphs = {}
    for idx,infoTuple in enumerate(listChamberAndScanDate):
        # Setup the path
        dirPath = getDirByAnaType("sbitRateor", infoTuple[0])
        if not filePathExists(dirPath, infoTuple[1]):
            print 'Filepath %s/%s does not exist!'%(dirPath, infoTuple[1])
            print 'Please cross-check, exiting!'
            exit(os.EX_DATAERR)
        filename = "%s/%s/SBitRatePlots.root"%(dirPath, infoTuple[1])

        # Load the file
        r.TH1.AddDirectory(False)
        scanFile   = r.TFile(filename,"READ")

        if scanFile.IsZombie():
            print("{0} is a zombie!!!".format(filename))
            print("Please double check your input list of scandates: {0}".format(args.filename))
            print("And then call this script again")
            raise IOError

        ###################
        # Get individual distributions
        ###################
        for vfat in range(24):
            dict_Histos[infoTuple[2]][vfat] = scanFile.Get("VFAT{0}/THR_ARM_DAC/g1D_rate_vs_THR-ARM-DAC_vfat{0}".format(vfat))
            dict_Graphs[infoTuple[2]][vfat] = r.TGraph(dict_Histos[infoTuple[2]][vfat])

            # Do we convert x-axis to charge units?
            if arrayCalInfo is not None:
                for pt in range(dict_Graphs[infoTuple[2]][vfat].GetN()):
                    valX = r.Double()
                    valY = r.Double()
                    dict_Graphs[infoTuple[2]][vfat].GetPoint(pt, valX, valY)
                    valX_Q=0
                    for coef in range(0,5):
                        valX_Q+=arrayCalInfo[coef][vfat] * pow(valX,4-coef)
                    dict_Graphs[infoTuple[2]][vfat].SetPoint(pt, valX_Q, valY)
                    pass
                pass

            # Make the TMultiGraph Objects
            suffix = "VFAT{0}".format(vfat)
            if idx == 0:
                dict_MultiGraphs[vfat] = r.TMultiGraph("mGraph_RateVsThrDac_vfat{0}".format(suffix),suffix)

            # Set Style of TGraph
            dict_Graphs[infoTuple[2]][vfat].SetLineColor(getCyclicColor(idx))
            dict_Graphs[infoTuple[2]][vfat].SetMarkerColor(getCyclicColor(idx))
            dict_Graphs[infoTuple[2]][vfat].SetMarkerStyle(20+idx)
            dict_Graphs[infoTuple[2]][vfat].SetMarkerSize(0.8)

            # Add to the MultiGraph
            dict_MultiGraphs[vfat].Add(dict_Graphs[infoTuple[2]][vfat])

            ###################
            # Make an entry in the TLegend
            ###################
            if vfat == 0:
                legPlot.AddEntry(
                        dict_Graphs[infoTuple[2]][vfat],
                        "{0} = {1}".format(thrDacName, infoTuple[2]),
                        "LPE")
                pass
            pass

    ###################
    # Make output ROOT file
    ###################
    outFileName = "{0}/compSbitThresh_{1}.root".format(elogPath,chamberName)
    outFile = r.TFile(outFileName,"RECREATE")

    # Plot Containers
    dict_canv = {}

    ###################
    # Now Make plots
    ###################

    for vfat in range(24):
        # Make Output Canvas
        dict_canv[vfat] = r.TCanvas("canvSBitRate_VFAT{0}".format(vfat),"SBIT Rate by THR DAC",700,700)
        dict_canv[vfat].cd()
        dict_canv[vfat].cd().SetLogy()
        dict_MultiGraphs[vfat].Draw("APE1")
        dict_MultiGraphs[vfat].GetYaxis().SetTitle("Rate #left(Hz#right)")
        dict_MultiGraphs[vfat].GetYaxis().SetRangeUser(1e-1,5e8) # max is 40 MHz
        if arrayCalInfo is not None:
            dict_MultiGraphs[vfat].GetXaxis().SetTitle("Threshold #left(fC#right)")
            dict_MultiGraphs[vfat].GetXaxis().SetRangeUser(0,20)
        else:
            dict_MultiGraphs[vfat].GetXaxis().SetTitle("CFG_THR_ARM_DAC #left(DAC#right)")
            dict_MultiGraphs[vfat].GetXaxis().SetRangeUser(0,125)
            pass
        dict_MultiGraphs[vfat].Draw("APE1")
        dict_canv

        # Draw Legend?
        if not args.noLeg:
            legPlot.Draw("same")
            pass

        # Make output image?
        if args.savePlots:
            dict_canv[vfat].SaveAs("{0}/{1}.png".format(elogPath,dict_canv[vfat].GetName()))
            pass

        # Store Output
        thisDirectory = outFile.mkdir("VFAT{0}".format(vfat))
        thisDirectory.cd()
        dict_MultiGraphs[vfat].Write()
        dict_canv[vfat].Write()
        pass

    # Make summary canvases, always save these
    canvSBitRate_Summary = make3x8Canvas("canvSBitRate_Summary",dict_MultiGraphs.values()[0:24],"APE1")
    for vfatCanv in range(1,25):
        canvSBitRate_Summary.cd(vfatCanv).SetLogy()
                
    # Draw Legend?
    if not args.noLeg:
        canvSBitRate_Summary.cd(1)
        legPlot.Draw("same")
        pass

    # Save summary canvases (always)
    print("\nSaving Summary TCanvas Objects")
    canvSBitRate_Summary.SaveAs("{0}/{1}.png".format(elogPath,canvSBitRate_Summary.GetName()))

    # Close output files
    outFile.Close()
    
    print("You can find all ROOT objects in:")
    print("\n\t{0}/compSbitThresh_{1}.root\n".format(elogPath,chamberName))

    print("You can find all plots in:")
    print("\n\t{0}\n".format(elogPath))

    print("Done")

    return

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Arguments to supply to plotSbitThreshComp.py')
    parser.add_argument("filename", type=str, help="Tab delimited filename specifying list of scandates to compare. First line understood as column header.  First column is chamber_name, second is scandate, and third will be used to fill a TLegend.  See documentation for parseListOfScanDatesFile(...) for more details")

    parser.add_argument("-a","--alphaLabels", action="store_true",help="Provide this argument if alphanumeric characters exist in the third column of the input file")
    parser.add_argument("-c","--calFileARM", type=str, 
            help="File specifying CFG_THR_ARM_DAC calibration per vfat.  If provided x-axis of each VFAT will be converted from DAC units to charge units (fC).  Format of file follows from TTree::ReadFile() with branch names: 'vfatN/I:coef4/F:coef3/F:coef2/F:coef1/F:coef0/F'", default=None)
    parser.add_argument("-n","--noLeg", action="store_true",
            help="Do not draw a TLegend on the output plots")
    parser.add_argument("-s","--savePlots", action="store_true",
            help="Make *.png file for all plots that will be saved in the output TFile")
    parser.set_defaults(func=compareSBitThreshResults)
    args = parser.parse_args()
    args.func(args)

    print("Goodbye")
