# -*- coding: utf-8 -*-
"""
Created on Thu Jun 27 13:30:26 2019

@author: mtjansen
"""

import sys
import os
import csv
import shutil
import time
import random

from collections import Counter
from PIL import Image, ImageChops, ImageStat
from scipy.ndimage import interpolation as inter
import numpy as np

sys.path.append(os.path.abspath(r"C:\Users\mtjansen\Desktop\OnTheBooks"))
from cropfunctions import *

os.chdir(r"C:\Users\mtjansen\Desktop\OnTheBooks\1865-1968 jp2 files")

############################
# Get xml data from file. ##
############################
master = []

with open(r"..\xmljpegmerge_official.csv", "r") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        row_dict = dict()
        row_dict["filename"] = row["filename"] + ".jp2"
        row_dict["side"] = row["handSide"].lower()
        row_dict["folder"] = row["filename"].split("_")[0]+"_jp2"
        row_dict["type"] = row['sectiontype']
        row_dict["start_section"] = False
        master.append(row_dict)
        
master = sorted(master, key = lambda i: i['filename']) 

for k in range(1,len(master)):
    if master[k]["type"] != master[k-1]["type"]:
        master[k]["start_section"] = True

master = [m for m in master if "186465" not in m["filename"]]
# Process metadata
    
#test = random.sample(master,500)
batch = master[80000:]
meta = []

img_ct = 0
start = time.time()
for r in batch:
    #t0 = time.time()
    f = os.path.join(r["folder"],r["filename"])
    orig = Image.open(f)
    
    side = r["side"]
        
    ang = rotation_angle(orig)
    
    if r["start_section"]:
        diff, background, orig_bbox = trim(orig, angle=ang, find_top=False)
    else:
        diff, background, orig_bbox = trim(orig, angle=ang)

    if "196" in r["folder"] or "195" in r["folder"]:
        total_bbox = orig_bbox
        cut = None
    else:
        bheight = 50
        band_dict = get_bands(diff, bheight=bheight) 
        
        width = diff.size[0]
        cut = simp_bd(band_dict=band_dict, diff=diff, side=side, width=width,
                      pad=10, freq =0.9)
    
        out_bbox = [0, 0] + list(diff.size)
        side_dict = {"left":0, "right":2}
        out_bbox[side_dict[side]] = cut
        
        total_bbox = combine_bbox(orig_bbox,out_bbox)
    
    meta_list = [r["filename"], ang, side, cut]
    meta_list.extend(background)
    meta_list.extend(total_bbox)
    meta.append(meta_list)
    img_ct +=1
    #print (r["filename"], time.time() - t0)
    if img_ct % 100 ==0:
        print(img_ct, time.time()- start)

headers = ["file","angle","side","cut","backR","backG","backB",
           "bbox1","bbox2","bbox3","bbox4"]
with open("..\marginalia_metadata_part2.csv","a",newline="") as outfile:
    writer=csv.writer(outfile)
    for row in meta:
        writer.writerow(row)

