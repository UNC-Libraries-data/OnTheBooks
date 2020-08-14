# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 08:16:57 2019

@author: mtjansen, npbyers
"""

from PIL import Image, ImageDraw
import os
import sys

sys.path.append(os.path.abspath("./"))
from cropfunctions import *

def bandimage(orig, angle, band_dict, bheight, orig_bbox):
        bd_ct = len(band_dict["band_bboxes"])
        back_height = bd_ct*(bheight+20)+100        
        img = orig.copy().rotate(angle).crop(orig_bbox)
        bounds = Image.new(orig.mode, orig.size, "white")
        draw = ImageDraw.Draw(bounds)

        for row in band_dict["band_bboxes"]:
            band_bbox = list(row["raw"])
            band_bbox[1] = row["index"]-50
            band_bbox[3] = row["index"]
            band = combine_bbox(orig_bbox,band_bbox)
            spot = tuple(list(band)[0:2])
            bounds.paste(img.crop(band_bbox),spot)
            if list(band_bbox)[2]-list(band_bbox)[0]>10:
                draw.rectangle(band,outline="red",fill = None,width=2)
            
        return bounds
    
def diffbands(diff, band_dict, cut, bheight):
        cdiff = diff.convert(mode="RGB")

        bd_ct = len(band_dict["band_bboxes"])
        back_height = bd_ct*(bheight+20)+100        
        bounds = Image.new(cdiff.mode, cdiff.size, "white")
        drawBands = ImageDraw.Draw(bounds)


        for row in band_dict["band_bboxes"]:
            band_bbox = list(row["raw"])
            band_bbox[1] = row["index"]-50
            band_bbox[3] = row["index"]
            spot = tuple(list(band_bbox)[0:2])
            bounds.paste(diff.crop(band_bbox),spot)
            if list(band_bbox)[2]-list(band_bbox)[0]>10:
                drawBands.rectangle(band_bbox,outline="#fc8003", fill = None,width=2)

        drawCut = ImageDraw.Draw(bounds)
        drawCut.line((cut,0, cut, bounds.size[1]),fill ="#0f03fc",width = 7)
            
        return bounds

def bandsdisplay(bandimages):
        back_width = (bandimages[0].size[0]+bandimages[1].size[0]+bandimages[2].size[0]+200)
        back_height = (max([bandimages[0].size[1], bandimages[1].size[1], bandimages[2].size[1]])+100)
        back = Image.new(bandimages[0].mode, (back_width,back_height), "white")

        back.paste(bandimages[0],(50,50))
        back.paste(bandimages[1],(bandimages[0].size[0]+100,50))
        back.paste(bandimages[2],(bandimages[0].size[0]+bandimages[1].size[0]+150,50))
        
        rs = back.resize((int(back.size[0]/5),int(back.size[1]/5)))
        
        
        return rs

    
def comparison1(orig, diff, angle, orig_bbox):
        img = orig.copy().convert(mode="RGBA")
        box=Image.new('RGBA', (img.size[0],img.size[1]))
        d = ImageDraw.Draw(box)
        d.rectangle(orig_bbox,outline="red",fill = None,width=5)
        w=box.rotate(-angle)

        superimpose = Image.new('RGBA', (img.size[0],img.size[1]))
        superimpose.paste(img, (0,0))
        superimpose.paste(w, (0,0), mask=w)

        back_width = (img.size[0]+diff.size[0]+150)
        back_height = (img.size[1]+100)
        back = Image.new(img.mode, (back_width,back_height), "white")
        draw = ImageDraw.Draw(img)

        back.paste(superimpose,(50,50))
        back.paste(diff,(superimpose.size[0]+100,orig_bbox[1]+50))
        
        rs = back.resize((int(back.size[0]/5),int(back.size[1]/5)))
        return rs
    
def comparison2(band, final):
        back_width = (band.size[0]+final.size[0]+150)
        back_height = (band.size[1]+100)
        back = Image.new(final.mode, (back_width,back_height), "white")

        back.paste(band,(50,50))
        back.paste(final,(band.size[0]+100,50))
        
        rs = back.resize((int(back.size[0]/5),int(back.size[1]/5)))
        return rs
    
def origdisplay(orig1, orig2, orig3):
        back_width = (orig1.size[0]+orig2.size[0]+orig3.size[0]+200)
        back_height = (max([orig1.size[1], orig2.size[1], orig3.size[1]])+100)
        back = Image.new(orig1.mode, (back_width,back_height), "white")

        back.paste(orig1,(50,50))
        back.paste(orig2,(orig1.size[0]+100,50))
        back.paste(orig3,(orig1.size[0]+orig2.size[0]+150,50))
        
        rs = back.resize((int(back.size[0]/5),int(back.size[1]/5)))
        return rs
    
def diffdisplay(diff1, diff2, diff3):
        img1 = diff1.copy().convert(mode="RGBA")
        img2 = diff2.copy().convert(mode="RGBA")
        img3 = diff3.copy().convert(mode="RGBA")
        back_width = (img1.size[0]+img2.size[0]+img3.size[0]+200)
        back_height = (max([img1.size[1], img2.size[1], img3.size[1]])+100)
        back = Image.new(img1.mode, (back_width,back_height), "white")

        back.paste(img1,(50,50))
        back.paste(img2,(img1.size[0]+100,50))
        back.paste(img3,(img1.size[0]+img2.size[0]+150,50))
        
        rs = back.resize((int(back.size[0]/5),int(back.size[1]/5)))
        return rs

def finalsdisplay(finalimages):
        #IN USE
        back_width = (finalimages[0].size[0]+finalimages[1].size[0]+finalimages[2].size[0]+200)
        back_height = (max([finalimages[0].size[1], finalimages[1].size[1], finalimages[2].size[1]])+100)
        back = Image.new(finalimages[0].mode, (back_width,back_height), "white")

        back.paste(finalimages[0],(50,50))
        back.paste(finalimages[1],(finalimages[0].size[0]+100,50))
        back.paste(finalimages[2],(finalimages[0].size[0]+finalimages[1].size[0]+150,50))
        
        rs = back.resize((int(back.size[0]/5),int(back.size[1]/5)))
        return rs
    