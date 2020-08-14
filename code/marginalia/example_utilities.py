# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 08:16:57 2019

@author: mtjansen
"""

from PIL import Image, ImageDraw
import os
import csv

sys.path.append(os.path.abspath(r"C:\Users\mtjansen\Desktop\OnTheBooks"))
from cropfunctions import *


def combine_bbox(b1,b2):
    """Combines successive boundary boxes, each within the last.
    Returns:
    tuple: Coordinates of crop (left,upper,right,lower)
    """
    b1 = list(b1)
    b2 = list(b2)
    total=[b1[k] + b2[k] for k in range(2)] + [b1[k-2] + b2[k] for k in range(2,4)]
    return tuple(total)

def example_image(orig, diff, angle, band_dict, bheight, total_bbox, orig_bbox):
        bd_ct = len(band_dict["hbands"])
        back_height = bd_ct*(bheight+20)+100        
        
#        bounds = Image.new(orig.mode, (orig.size[0],back_height), "white")
#        
#        for row in band_dict["hbands"]:
#            band_bbox = list(row["raw"])
#            band_bbox[1] = row["index"]
#            band_bbox[3] = row["index"]+50
#            band = orig.crop(orig_bbox).crop(tuple(band_bbox))
#            hoff = list(row["raw"])[0] + list(orig_bbox)[0]
#            voff = row["index"] + list(orig_bbox)[1]+10*(row["index"]+50)/bheight
#            bounds.paste(band,(hoff,int(voff)))
        
        img = orig.copy().rotate(angle).crop(orig_bbox)
        bounds = Image.new(orig.mode, orig.size, "white")
        draw = ImageDraw.Draw(bounds)

        for row in band_dict["hbands"]:
            band_bbox = list(row["raw"])
            band_bbox[1] = row["index"]-50
            band_bbox[3] = row["index"]
            band = combine_bbox(orig_bbox,band_bbox)
            spot = tuple(list(band)[0:2])
            bounds.paste(img.crop(band_bbox),spot)
            if list(band_bbox)[2]-list(band_bbox)[0]>10:
                draw.rectangle(band,outline="red",fill = None,width=2)
            
        final = orig.rotate(angle).crop(total_bbox)
        
        back_width = (orig.size[0]+bounds.size[0]+final.size[0])+250
        back = Image.new(orig.mode, (back_width,back_height), "white")
        
        back.paste(orig,(50,50))
        back.paste(bounds,(orig.size[0]+150,50))
        back.paste(final,(orig.size[0]+bounds.size[0]+250,list(total_bbox)[1]+50))
        
        return back
        
    
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
    
batch = [row for row in master if row["filename"] in ["publiclocallawsp1917nort_0568.jp2","publiclocallawsp1933nort_0063.jp2"]]

output_dir = r"C:\Users\mtjansen\Desktop\OnTheBooks\outwide_fix"
for r in batch:
    t0 = time.time()
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
    
    ex = example_image(orig=orig, diff=diff, angle=ang, band_dict=band_dict, 
                  bheight=bheight, total_bbox=total_bbox, orig_bbox=orig_bbox)
    
    out = os.path.join(output_dir,r["filename"].replace(".jp2","_BREAK.jpg"))
    ex.save(out, "JPEG")
    