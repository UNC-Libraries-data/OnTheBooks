# -*- coding: utf-8 -*-
"""
Created on Fri Jul  5 09:11:57 2019

@author: mtjansen
"""

import csv
import os
from PIL import Image

meta = []
with open(r"C:\Users\mtjansen\Desktop\OnTheBooks\marginalia_metadata.csv","r") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        meta.append(row)

def remove_marginalia(img, meta, image_directory, file_output=False, output_directory = None):
    """Uses marginalia metadata to crop image and add border.
    
    Parameters:
    img (str): image file name with or without .jp2 file ending
    metadata (str): list of dicts from "marginalia_metadata.csv" with keys:
        file: file path with extension
        angle: angle of rotation
        backR: Red channel of background color in RGB
        backG: Green channel of background color in RGB
        backB: Blue channel of background color in RGB
        bbox1: First coordinate of bounding box (left)
        bbox2: Second coordinate of bounding box (top)
        bbox3: Third coordinate of bounding box (right)
        bbox4: Fourth coordinate of bounding box (bottom)
    image_directory (str): path to directory containing volue subfolders e.g.
        1865-1968 jp2 files\sessionlaws196365nort_jp2\sessionlaws196365nort_0000.jp2
        The path above maps to a single image, therefore the path to 
        1865-1968 jp2 files should be supplied to image_directory
    file_output (logical): whether to locally save a jpg version of the 
        cropped image
    output_directory (str): path to directory to save output images if indicated
        by file_output.  Directory structure will mirror the input directories
        in image_directory
        
    Returns:
    PIL.Image.Image: An image cropped as indicated in meta, with a 200 pixel wide
        border filled in with the supplied background color in meta.
        If file_output is selected, a jpg version of the cropped image will be saved
            to output_directory.
    """

    try:
        if not img.endswith(".jp2"):
            img = img+".jp2"
        row = [r for r in meta if r["file"]==img][0]
        path = os.path.join(image_directory,
                            row["file"].split("_")[0]+"_jp2",
                            row["file"])
        background = tuple([int(n) for n in [row["backR"],row["backG"],
                            row["backB"]]])
        bbox = tuple([int(n) for n in [row["bbox1"],row["bbox2"],
                      row["bbox3"],row["bbox4"]]])
        orig = Image.open(path)
        new = orig.rotate(float(row["angle"])).crop(bbox)
        outimg = Image.new(orig.mode, tuple(x+400 for x in new.size), background)
        offset = (200, 200)
        outimg.paste(new, offset)
        
        if file_output:
#            out = os.path.join(output_dir,
#                               row["file"].split("_")[0]+"_jp2",
#                               row["file"])
#            if not (os.path.exists(os.path.split(out)[0])):
#                os.mkdir(os.path.split(out)[0])
            out = os.path.join(output_dir,
                               row["file"].replace(".jp2",".jpg"))
            outimg.save(out, "JPEG")
        
        return outimg
    except:
        print("Image not found in metadata")

    
    
#Test
image_dir = r"C:\Users\mtjansen\Desktop\OnTheBooks\1865-1968 jp2 files"
output_dir = r"C:\Users\mtjansen\Desktop\OnTheBooks\out_width"

#import random
#test_set = random.sample(meta,500)

outliers = []
with open(r"C:\Users\mtjansen\Desktop\OnTheBooks\outlier_metadata_width.csv","r") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        outliers.append(row)
        
#test_set = [row for row in meta if row["file"] in ["publiclocallawsp1917nort_0568.jp2","publiclocallawsp1933nort_0063.jp2"]]
#        
#test_set = random.sample(outliers,100)
        

for row in outliers:
    img = remove_marginalia(img = row["file"],
                      meta = outliers,
                      image_directory = image_dir,
                      file_output = True,
                      output_directory = output_dir)
    
for row in test_set:
    path = os.path.join(image_directory,
                            row["file"].split("_")[0]+"_jp2",
                            row["file"])
    out = os.path.join(output_dir,
                               row["file"].replace(".jp2",".jpg"))
    
    background = tuple([int(n) for n in [row["backR"],row["backG"],
                    row["backB"]]])
    bbox = tuple([int(n) for n in [row["bbox1"],row["bbox2"],
              row["bbox3"],row["bbox4"]]])
    
    orig = Image.open(path)
    new = orig.rotate(float(row["angle"])).crop(bbox)
    outimg = Image.new(orig.mode, tuple(x+400 for x in new.size), background)
    offset = (200, 200)
    outimg.paste(new, offset)
    outimg.save(out, "JPEG")