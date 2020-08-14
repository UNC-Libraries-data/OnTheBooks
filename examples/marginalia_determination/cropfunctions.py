# -*- coding: utf-8 -*-
"""
Created on Thu Jun 27 13:31:02 2019

@author: mtjansen
"""
from collections import Counter

from PIL import Image, ImageChops, ImageStat
from scipy.ndimage import interpolation as inter
import numpy as np


def combine_bbox(b1,b2):
    """Combines two boundary boxes, using the second set of coordinates to crop into the first
    Returns:
    tuple: Coordinates of crop (left,upper,right,lower)
    """
    b1 = list(b1)
    b2 = list(b2)
    total=[b1[k] + b2[k] for k in range(2)] + [b1[k-2] + b2[k] for k in range(2,4)]
    return tuple(total)

def buffer_bbox(bbox,buff,width,height):
    """Expands a boundary box in all directions by a set number of pixels.
    
    Parameters:
    bbox (tuple): A boundary box
    buff (int): The number of pixels to expand bbox by
    width (int): This is the width of the image to be cropped by bbox
    height (int): This is the height of the image to be cropped by bbox
    """
    bbox = list(bbox)
    new_bbox = [0,0,width,height]
    new_bbox[0] = max(bbox[0]-buff,0)
    new_bbox[1] = max(bbox[1]-buff,0)
    new_bbox[2] = min(bbox[2]+buff,width)
    new_bbox[3] = min(bbox[3]+buff,height)
    return tuple(new_bbox)

def strip_list(list_of_bboxes, pos):
    """Extracts all elements in the pos index of for lists within lists.
    Intended to extract bands from the left or right side of PIL bboxes,
    then remove any one-off values.

    Parameters:
    list_of_bboxes (list): List of bboxes (lists)
    pos (int): Index of bbox item to extract

    Returns:
    list: list of pos-indexed values from each bbox, with one-off values removed
    """

    filtered = [x[pos] for x in filter(None, list_of_bboxes)]
    keep = {}
    for i in filtered:
        keep[i] = i in keep
    return [e for e in filtered if keep[e]]

## find_score and rotation_angle derived from:
## https://avilpage.com/2016/11/detect-correct-skew-images-python.html

def find_score(arr, angle):
    """Determine score for a given rotation angle.
    """
    data = inter.rotate(arr, angle, reshape=False, order=0)
    hist = np.sum(data, axis=1)
    score = np.sum((hist[1:] - hist[:-1]) ** 2)
    return hist, score

def rotation_angle(img):
    """Determine the best angle to rotate the image to remove skew.
    
    Parameters:
    img (PIL.Image.Image): Image
    
    Returns:
    (int): Angle
    """
    wd, ht = img.size
    pix = np.array(img.convert('1').getdata(), np.uint8)
    bin_img = 1 - (pix.reshape((ht, wd)) / 255.0)
   
    delta = 0.25
    limit = 1
    angles = np.arange(-limit, limit+delta, delta)
    scores = []
    for angle in angles:
        hist, score = find_score(bin_img, angle)
        scores.append(score)
    
    best_score = max(scores)
    best_angle = angles[scores.index(best_score)]
    
    return float(best_angle)


def trim(img, angle=0, buff=10, find_top=True):
    """Determines background color and bounding box to crop image to text

    Parameters:
    img (PIL.Image.Image): Image
    angle (float): Degrees to rotate the image
    buff (int): Horizontal buffer used to expand the bounding box
    find_top (Boolean): Whether to attempt to crop the header
    
    
    Returns:
    PIL.Image.Image: Original image, with background color removed, cropped to area containing text
    tuple: Derived average background color, in same mode as original image
    tuple: Coordinates of crop (left,upper,right,lower)
    """

    width, height = img.size
    
    background = tuple(ImageStat.Stat(img).median)

    bg = Image.new(mode = img.mode, size = img.size, color = background)
    diff = ImageChops.difference(img, bg)
    offset = round(max(ImageStat.Stat(diff).stddev) * 3)
    diff = ImageChops.add(diff, diff, 2.0, - offset).convert("1")
    
    if angle !=0:
        diff = diff.rotate(angle)
    
    
    bbox = diff.getbbox()
    if find_top:
        top = 0
        for k in range(50,361,30):
            try:
                h = diff.crop(bbox).crop((round(width/5),0,round(4*width/5),k)).getbbox()[3]
                if top == h and h >= 20:
                    #check h>=20 to avoid small watermarks, characters are
                    #usually taller than 20 pixels
                    break
                elif h != k:
                    top = h
            except:
                pass
    
        bbox = list(bbox)
        bbox[1] += top+buff
        bbox1 = diff.crop(tuple(bbox)).getbbox()
        
        bbox = combine_bbox(bbox,bbox1)
    
    bbox = buffer_bbox(bbox = bbox, buff = buff, width = width, height = height)

    if bbox:
        return diff.crop(bbox), background, bbox
    else:
        return None


def get_bands(img, bheight=50, skip=0, rd=20):
    """Divides image into horizontal strips and determines bbox for each strip.

    Parameters:
    im (PIL.Image.Image): Image
    bheight (int): Height of each horizontal strip. Recommend using
    approximately the height of a line of text.
    skip (int): skip the first <skip> pixels of the image when creating bands.
    rd (int): bounded values are also provided rounded to the nearest <rd> units.

    Returns:.
    dict: A dictionary with the following keys:
            "band_bboxes": A list of dictionaries, each representing one band and
               containing three keys:
                    "index": The pixel coordinate of the bottom of the band
                    "raw": The raw bounding box for that band
                    "round": The bounding box rounded to the nearest <rd> pixels for
                             the left and right coordinates
            "rd": The parameter <rd> used
    """

    width, height = img.size
    band_bboxes = []
    for w in range(skip+bheight, height-skip, bheight):
        rdict = dict()
        rdict["index"] = w
        bb = img.crop((0, w-bheight, width, w)).getbbox()
        if bb != None:
            rdict["round"] = (round(bb[0]/rd) * rd, bb[1], round(bb[2]/rd) * rd, bb[3])
            rdict["raw"] = bb
            band_bboxes.append(rdict)
        else:
            rdict["raw"] = None
            rdict["round"] = None
            band_bboxes.append(rdict)

    # nulls identifies rows with None values and all rows neighbouring a None value for removal
    nulls = [k for k in range(len(band_bboxes)) if band_bboxes[k]["raw"] == None]
    nulls += [(k+1) for k in nulls if k < len(band_bboxes) and (k+1) not in nulls]
    nulls += [(k-1) for k in nulls if k > 0 and (k-1) not in nulls]

    return {"band_bboxes":[band_bboxes[k] for k in range(len(band_bboxes)) if k not in nulls],
            "rd":rd}

def simp_bd(band_dict, diff, side, width, pad=10, allow=(0.1, 0.3), freq=0.8, 
            minfreq=0.1):
    """Converts bands generated by get_bands into a pixel location to cut the
    image vertically.

    Parameters:
    band_dict (list): output from get_bands, a dictionary containing:
        "band_bboxes": list of dictionaries with keys:
            "raw": bounding box for corresponsing band.
            "round": bounding box for corresponding band, rounded to the nearest <rd>
        "rd": the rounding distance used in get_bands
    diff (PIL.Image.Image): Original image, with background color removed, 
        cropped to area containing text
    side (str): output from get_bands, which side is marginalia located on?
    width (int): pixel width of image to cut
    pad (int): reduces (left) or increases (right) cut location.  This can
        account for slight tilt or otherwise aggressive outputs.
    allow (list): Two (float) elements:
        allow[0] = minimium width of marginalia from edge
        allow[1] = maximum width of marginalia from edge
            e.g. allow = [0.1,0.3] means right marginalia is
            between 0.7*width and 0.9*width.
    freq (float): If one value represents a proportion of all values greater than
        <freq>, it is automatically selected as the cut location (then adjusted
        by <pad>)
    minfreq (float): A value must appear in a proportion of at least <minfreq>
        to be considered.

    Returns:
    int: A pixel location to separate marginalia from the main text.  If the
        algorithm fails, this location may be the 0 or the width (side-dependent).

    Details:
    The first part of this function isolates relevant values from the bounding
    boxes based on side, then removes "ineligible" candidates - those with
    one of the following, based on rounded values:
        - Location outside the range defined by <allow>
        - Location frequency less than <minfreq>
    This section returns all eligible candidates or only one candidate if its
    frequency is greater than <freq>.

    The second part of this function chooses the "best" candidate using the
    following algorithm:
        -
    """
    bands = [v["round"] for v in band_dict["band_bboxes"]]
    raw = [v["raw"] for v in band_dict["band_bboxes"]]
    rd_dist = band_dict["rd"]
    side_dict = {"left":0, "right":2}
    bands = strip_list(bands, side_dict[side])
    try:
        #1. Determine eligible candidates
        if side == "right":
            pixmin = width-allow[1] * width
            pixmax = width-allow[0] * width
            newbands = [b for b in bands if b > pixmin and b < pixmax]
            rev = True
        elif side == "left":
            pixmin = allow[0] * width
            pixmax = allow[1] * width
            newbands = [b for b in bands if b > pixmin and b < pixmax]
            rev = False

        if newbands:
            ct = Counter(sorted(newbands, reverse=rev))

            if ct.most_common(1)[0][1]/(sum([e for e in dict(ct).values()])) > freq:
                cut = [e[0] for e in ct.most_common(1)][0]
                if side == "right":
                    cut = min(cut + pad, width)
                elif side == "left":
                    cut = max(cut - pad, 0)
            else:
                m = [k for k in ct.keys() if ct[k] > len(newbands)*minfreq]
                cut_dict = {k:0 for k in m}
                if len(m)>1:
                    for cut in m:
                        text_bbox = [0, 0] + list(diff.size)
                        text_bbox[side_dict[side]] = cut
                        other = abs(side_dict[side]-2)
                        text_bbox[other] = (1-side_dict[side]) * (50)+cut
                        margin_bbox = [0, 0] + list(diff.size)
                        margin_bbox[side_dict[side]] = (side_dict[side]-1) * (50)+cut
                        margin_bbox[other] = cut
                        mean_diff = np.mean(diff.crop(text_bbox)) - np.mean(diff.crop(margin_bbox))
                        cut_dict[cut] += mean_diff
                    cutrange = max(cut_dict, key=cut_dict.get)
                elif len(m)==1:
                    cutrange = m[0]
                pix_list = [i[side_dict[side]] for i in raw if abs(i[side_dict[side]]-cutrange) < rd_dist/2]
    
                #2. Choose best candidate
                if side == "right":
                    cut = min(max(pix_list)+pad, width)
    
                elif side == "left":
                    cut = max(min(pix_list)-pad, 0)
        else:
            #print("NO ELIGIBLE CUTS")
            if side == "right":
                cut = width
            elif side == "left":
                cut = 0

        return cut

    except:
        if side == "left":
            return 0
        elif side == "right":
            return width