#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 15:18:26 2019

@author: Lorin Bruckner

Digital Research Services
University Libraries
UNC Chapel Hill
"""

import os, sys
import pandas as pandas
from datetime import datetime

#get ocr functions
sys.path.insert(0, "/Users/tuesday/Documents/_Projects/Research/OnTheBooks/OCR/")
from ocr_func import cutMarg, adjustImg, tsvOCR

#Set up locations
masterlist = "/Users/tuesday/Documents/_Projects/Research/OnTheBooks/xmljpegmerge_official.csv"
margdata = "/Users/tuesday/Documents/_Projects/Research/OnTheBooks/marginalia_metadata_part2_fix.csv"
adjdata = "/Users/tuesday/Documents/_Projects/Research/OnTheBooks/adjustments_fixed.csv"
rootImgDir = "/Users/tuesday/Documents/_Projects/Research/OnTheBooks/1865-1968 jp2 files/"        
outDir = "/Users/tuesday/Documents/_Projects/Research/OnTheBooks/output/"

#Read csvs
mastercsv = pandas.read_csv(masterlist)
margcsv = pandas.read_csv(margdata)
adjcsv = pandas.read_csv(adjdata)

#Create column for volume
for index, row in mastercsv.iterrows():
    volume = row["filename"].split("_")[0]
    mastercsv.at[index, "volume"] = volume  

#Merge csvs
mastercsv["filename"] = mastercsv["filename"] + ".jp2" 
mcsv = mastercsv.merge(margcsv, left_on="filename", right_on="file")
fcsv = mcsv.merge(adjcsv, on = "volume", how = "right")

#get separate volumes
volsGrouped = fcsv.groupby("volume")
vols = volsGrouped.groups.keys()

#loop through volumes
for vol in vols:
    
    print("")
    
    #create a folder for the volume in the output directory if it doesn't already exist
    newdir = os.path.normpath(os.path.join(outDir, vol))
    if os.path.exists(newdir) == False:
        os.mkdir(newdir)
    
    #select rows for volume
    voldf = volsGrouped.get_group(vol)
    
    #get separate section types
    secsGrouped = voldf.groupby("sectiontype")
    secs = secsGrouped.groups.keys()
    
    #create seperate OCR files for each section
    for sec in secs:
            
        #select rows for section type
        secsdf = secsGrouped.get_group(sec)

        print(datetime.now().strftime("%H:%M") + " Processing " + vol + " " + sec + "...")
        
        #Loop through section
        for row in secsdf.itertuples():
            
            img = os.path.normpath(os.path.join(rootImgDir, vol + "_jp2", row.file))
            
            #set up margin cutting
            cuts = {"rotate" : row.angle,
                    "left" : row.bbox1,
                    "up" : row.bbox2,
                    "right" : row.bbox3,
                    "lower" : row.bbox4,
                    "border" : 200,
                    "bkgcol" : (row.backR, row.backG, row.backB)}
            
            #set up image adjustment            
            adjustments = {"color": row.color, 
                           "autocontrast": row.autocontrast,
                           "blur": row.blur,
                           "sharpen": row.sharpen,
                           "smooth": row.smooth,
                           "xsmooth": row.xsmooth}
            
            #Record image adjustments
            adjf = open(os.path.normpath(os.path.join(outDir, vol, vol + "_adjustments.txt")), "w")
            adjf.write("IMAGE ADJUSTMENTS\n\n")
            for key, value in adjustments.items():
                adjf.write("{}: {}\n" .format(key, value))
            adjf.close()
            
            #OCR the image
            tsvOCR((adjustImg(cutMarg(img, **cuts), **adjustments)), 
                   savpath = os.path.normpath(os.path.join(outDir, vol, vol + "_" + sec + ".txt")), 
                   tsvfile = vol + "_" + sec + "_data.tsv")
 