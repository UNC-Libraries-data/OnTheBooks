#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 16:38:46 2019

@author: Lorin Bruckner

Digital Research Services
University Libraries
UNC Chapel Hill
"""

import os, sys
import pandas as pandas
from random import sample
import csv

#get ocr functions
sys.path.append(os.path.abspath("./"))
from ocr_func import cutMarg, OCRtestImg, testList

def adjRec(vol, dirpath, masterlist, margdata, n):
    
    """

    Get the best image adustments to use on a volume.     
  
    vol (str)        : The name for the volume to be tested. Should not include
                       "_jp2" (so for 1879, it's "lawsresolutionso1879nort")
                  
    dirpath (str)    : The directory path for the folder where ALL volumes are located
    
    masterlist (str) : The direct file path for xmljpegmerge_official.csv
    
    margdata (str)   : The direct file path for the csv with marginalia data
    
    n (int)          : The sample size to use for testing

    """

    #Merge csvs
    mastercsv = pandas.read_csv(masterlist)
    margcsv = pandas.read_csv(margdata)
    mastercsv["filename"] = mastercsv["filename"] + ".jp2" 
    csv = mastercsv.merge(margcsv, left_on="filename", right_on="file")
    
    #Create a pool of image filenames for the volume and take a sample
    pool = []
    csvf = csv[csv["filename"].str.startswith(vol)].set_index("filename")
    
    for row in csvf.itertuples():
        pool.append(os.path.normpath(os.path.join(dirpath, vol + "_jp2/" + row.file)))
    
    pool = sample(pool, n)  
    
    #Get images for files in sample, cut margins and make a test list
    imgs = []
    results = []
    
    for img in pool:
        
        #get image name
        name = os.path.split(img)[1]
        
        #get values for cutting margins
        rotate = csvf.loc[name]["angle"]
        left = csvf.loc[name]["bbox1"]
        up = csvf.loc[name]["bbox2"]
        right = csvf.loc[name]["bbox3"]
        lower = csvf.loc[name]["bbox4"]
        bkgcol = (csvf.loc[name]["backR"], csvf.loc[name]["backG"], csvf.loc[name]["backB"])
        
        #cut the margins          
        img = cutMarg(img = img, rotate = rotate, left = left, up = up, right = right,
                     lower = lower, border = 200, bkgcol = bkgcol)
        
        #add the new image to the list
        imgs.append(img)
        
        #perform an OCR test on the new image and add the results to the list
        results.append(OCRtestImg(img))
        
    #create a testList object with the  images and results
    testSample = testList(imgs, results)
    
    #set up a dict of reccommended adjustments and perform tests
    adjustments = { "volume": vol, "color": 1.0, "invert": False, 
                    "autocontrast": 0, "blur": False, "sharpen": False, 
                    "smooth": False, "xsmooth": False }

    #color test
    testRes = testSample.adjustTest("color", levels = [1,.75,.5,.25,0])
    best = float(testRes["best_adjustment"].replace("color", ""))
    if best != 1.0:
        testSample = testSample.adjustSampleImgs(color = best)
        adjustments["color"] = best
        
    #invert test
#    testRes = testSample.adjustTest("invert")
#    if testRes["best_adjustment"] == "invertTrue":
#        testSample = testSample.adjustImg(invert = True)
#        adjustments["invert"] = True
        
    #autocontrast test
    testRes = testSample.adjustTest("autocontrast", levels = [0,2,4,6,8])
    best = float(testRes["best_adjustment"].replace("autocontrast", ""))
    if best != 0.0:
        testSample = testSample.adjustSampleImgs(autocontrast = best)
        adjustments["autocontrast"] = best
        
    #blur test
    testRes = testSample.adjustTest("blur")
    if testRes["best_adjustment"] == "blurTrue":
        testSample = testSample.adjustSampleImgs(blur = True)
        adjustments["blur"] = True
        
    #sharpen test
    testRes = testSample.adjustTest("sharpen")
    if testRes["best_adjustment"] == "sharpenTrue":
        testSample = testSample.adjustSampleImgs(sharpen = True)
        adjustments["sharpen"] = True
        
    #smooth test
    testRes = testSample.adjustTest("smooth")
    if testRes["best_adjustment"] == "smoothTrue":
        testSample = testSample.adjustSampleImgs(smooth = True)
        adjustments["smooth"] = True
        
        #xsmooth test
        testRes = testSample.adjustTest("xsmooth")
        if testRes["best_adjustment"] == "xsmoothTrue":
            testSample = testSample.adjustSampleImgs(xsmooth = True)
            adjustments["xsmooth"] = True

    return adjustments    


###########  Set up locations  ###############################################
    
dirpath = "/images"     
masterlist = "SampleMetadata.csv"
margdata = "marginalia_metadata_demo.csv"


###########  Reccommend Adjustments for a Single Volume  ######################

adjDEMO = adjRec("lawsresolutionso1891nort", dirpath, masterlist, margdata, 3)


###########  Create a CSV with Adjustment Specs for all Volumes  ############## 

savfile = "/Users/tuesday/Documents/_Projects/Research/OnTheBooks/output/adjustmentsDEMO.csv"

for folder in os.listdir(dirpath):
    
    if folder == ".DS_Store":
        continue
    
    #get volume
    vol = folder.replace("_jp2", "")
    print ("Testing " + vol + "...")
    
    #peform adjustment tests 
    adjRow = adjRec(vol, dirpath, masterlist, margdata, 10)
    
    #record adjustments
    with open(savfile, "a") as f:
        w = csv.DictWriter(f, adjRow.keys())
        if f.tell() == 0:
            w.writeheader()
            w.writerow(adjRow)
        else: 
            w.writerow(adjRow)