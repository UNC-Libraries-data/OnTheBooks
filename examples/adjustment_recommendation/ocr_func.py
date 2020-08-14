#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 15:14:53 2019

@author: Lorin Bruckner

Digital Research Services
University Libraries
UNC Chapel Hill
"""


import pytesseract
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from spellchecker import SpellChecker
from nltk import word_tokenize
import os
from tqdm import tqdm
import pandas as pandas
from random import sample
from io import StringIO
from numpy import random
import csv

#establish tesseract directory
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

#show more columns in dataframes
pandas.set_option('display.max_columns', 999)

def cutMarg(img, rotate, left, up, right, lower, border, bkgcol):
    
    """
    
    Remove margins from an image.
    
    Rotates, then crops an image to the bounding box designated by the left, up,
    right and lower parameters. The border is then expanded and filled with a
    background color.
    
    Arguments
    --------------------------------------------------------------------------    
    img (str, PIL image) : Either the file path of an image or a PIL image object
                         
    rotate (float)       : Degrees of counter clockwise rotation in pixels
    
    left (float)         : Left edge of boundng box in pixels
    
    up (float)           : Upper edge of bounding box in pixels
    
    right (float)        : Right edge of bounding box in pixels
    
    lower (float)        : Lower edge of bounding box in pixels
    
    border (float)       : Number of pixels to expand the image border
    
    bkgcol (tuple)       : Tuple of RGB values to use as a background color
    
    Returns
    --------------------------------------------------------------------------
    A PIL image object.
    
    """
    
    name = ""
    
    #if a filename is used for the image, load the image
    if type(img) == str:
        name = os.path.split(img)[1]
        img = Image.open(img)
    else:
        name = img.info["name"]
    
    #rotate, crop, expand border and fill with color
    img = img.rotate(rotate)
    img = img.crop((left, up, right, lower))
    img = ImageOps.expand(img, border = border, fill = bkgcol)
    
    #return image with name info
    img.info = {"name" : name}
    return(img)
    
    
def adjustImg(img,  color = 1.0, brightness = 1.0, contrast = 1.0, 
              autocontrast = 0, sharpness = 1.0, invert = False, blur = False, 
              sharpen = False, smooth = False, xsmooth = False):
    
    """
    
    Opens an image, applies adjustments, and returns a new image. 
    
    Arguments
    --------------------------------------------------------------------------    
    img (str, PIL image) : Either the file path of an image or a PIL image object.
                         
    color (float)        : 0.0 gives a black and white image; 1.0 gives the 
                           original image.
                         
    brightness (float)   : 0.0 gives a black image; 1.0 gives the original image.
    
    contrast (float)     : 0.0 gives a solid grey image; 1.0 gives the 
                           original image.
    
    autocontrast (float) : removes given percent of lightest and darkest pixels
                           from image histogram, then remaps image so darkest 
                           remaining pixel becomes black (0), and lightest 
                           becomes white (255).
                         
    sharpness (float)    : 0.0 gives a blurred image; 1.0 gives the original 
                           image; 2.0 gives a sharpened image.
                         
    invert (bool)        : If True, inverts the image colors.
    
    blur(bool)           : If True, applies BLUR filter.
    
    sharpen(bool)        : If True, applies SHARPEN filter.
    
    smooth(bool)         : If True, applies SMOOTH filter.
     
    xsmooth(bool)        : If True, applies SMOOTH_MORE filter.

    Returns
    --------------------------------------------------------------------------
    A PIL image object.
    
    """
    
    name = ""
    
    #If a filename is used for the image, load the image
    if type(img) == str:
        name = os.path.split(img)[1]
        img = Image.open(img)
    else:
        name = img.info["name"]
        
    #Perform image adjustments.
    if color != 1.0:    
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(color)
        
    if invert == True:    
        img = ImageOps.invert(img)

    if autocontrast != 0:    
        img = ImageOps.autocontrast(img, cutoff = autocontrast)    
        
    if brightness != 1.0:    
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(brightness)
    
    if contrast != 1.0:    
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)
        
    if blur == True:    
        img = img.filter(ImageFilter.BLUR)

    if sharpen == True:    
        img = img.filter(ImageFilter.SHARPEN)
 
    if sharpness != 1.0:    
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(sharpness)
    
    if smooth == True:    
        img = img.filter(ImageFilter.SMOOTH)
    
    if xsmooth == True:    
        img = img.filter(ImageFilter.SMOOTH_MORE)
    
    #Return the image with name info
    img.info = {"name" : name}
    return(img)


def OCRtestImg(img, alltext = False, correct = False, psm = 1, oem = 3):
    
    """
    
    Test the accuracy of OCR when applied to an image.
    
    Opens an image and performs OCR using Tesseract. OCR'd text is then tokenized 
    with NLTK and compared to the SpellChecker dictionary. A record is created 
    for the image that includes filename, number of tokens, number of unknown 
    words, readability score and list of unknown words. 
    
    Arguments
    --------------------------------------------------------------------------    
    img (str, PIL image) : Either the file path of an image or a PIL image object.
                           If a PIL object is used, the info attribute must
                           contain a key called "name" assigned to a string
                           value.
    
    alltext (bool)       : If True, the full OCR text is included 
                           in the image record.
                          
    correct (bool)       : If True, a list of suggested corrections for
                           unknown words is included in the image record.
    
    psm (int)            : Tesseract configuration for Page Segmentation Mode. 
                           https://github.com/tesseract-ocr/tesseract/blob/master/doc/tesseract.1.asc
                         
    oem (int)            : Tesseract configuration for OCR Engine mode. 
                           https://github.com/tesseract-ocr/tesseract/blob/master/doc/tesseract.1.asc 
    
    Returns
    --------------------------------------------------------------------------
    (dict) The record for the image.
    
    """
    
    name = ""
    
    #if a filename is used for the image, load the image
    if type(img) == str:
        name = os.path.split(img)[1]
        img = Image.open(img)
        img.info = {"name" : name}
    else:
        name = img.info["name"]
        if img.info == {}:
            return "The info attribute for the PIL image object is empty. It must contain a \"name\" key assigned to a string value."
    
    # Set up tesseract config
    if 0 <= psm <= 13:
        pconfig = "--psm " + str(psm)
    else:
        return "Invalid tesseract config."
    
    if 0 <= oem <= 3:
        oconfig = "--oem " + str(oem)
    else:
        return "Invalid tesseract config."
    
    tconfig = pconfig + " " + oconfig
    
    #Perform cropping, image adjustments and OCR
    text = pytesseract.image_to_string(img, config = tconfig)
    
    #join hyphenated words that are split between lines
    text = text.replace("-\n","")
    
    #tokenize text, remove punctuation and convert to utf-8
    tokens = word_tokenize(text)
    tokens = [token for token in tokens if token.isalpha()]
    tokens = [token.encode("utf-8", errors = "replace") for token in tokens]
    
    #add NC geonames to spellchecker dictionary
    #(see geonames.py for script used to create the text file)
    spell = SpellChecker()
    spell.word_frequency.load_text_file("geonames.txt")
            
    #get unknown words
    unknown = spell.unknown(tokens)
    
    #create list of replacements for unknown words
    if correct == True:
        
        corrections = []
        
        for word in unknown:
            try:
                corrections.append(spell.correction(word))
            except:
                print("Ascii/unicode conversion issues came up but they were ignored.")
        
        corrections = [word.encode("utf-8", errors = "replace") for word in corrections]
        
    #Get readability score
    if len(unknown) != 0:
       readability = round(100 - (float(len(unknown))/float(len(tokens)) * 100), 3)
    else:
       readability = 100
    
    #create record for image
    imgRecord = {
            "name" : img.info["name"],
            "token_count" : len(tokens),
            "unknown_count" : len(unknown),
            "readability" : readability,
            "unknown_words" : list(unknown)
            }
    
    #add full OCR text if required
    if alltext == True:
        imgRecord["text"] = text.encode("utf-8", errors = "replace")
        
    #add spell checker corrections if required
    if correct == True:
        imgRecord["corrections"] = corrections

    
    return(imgRecord)
    

def mkOCRtestList(pool, n):
    
    """
    
    Create a testList object for testing a selection of images.
    
    Selects a random sample from a pool of image files and performs an initial
    OCR test. Returns a testList object for further testing.
    
    Arguments
    --------------------------------------------------------------------------    
    
    pool (list)             : A list of image file paths.
    
    n (int)                 : Sample size to be tested.
                    
    
    Returns
    --------------------------------------------------------------------------
    A testList object.
    
    """
    
    #create empty lists to store image records and image objects
    images = []
    results = []

    #Create a sample of image objects
    for filename in tqdm(sample(pool, n)):
        name = os.path.split(filename)[1]
        img = Image.open(filename)
        img.info = {"name" : name}
        images.append(img)
        results.append(OCRtestImg(img))

    testObj = testList(images, results)            
    return(testObj)

def OCRimg(img, savpath, append = True, psm = 1, oem = 3, adjdoc = True, **kwargs):
    
    """
    
    Run OCR on a PIL image object and produce a text file.
    
    Arguments
    --------------------------------------------------------------------------    
    img (str, PIL image) : Either the file path of an image or a PIL image object
    
    savpath (str)        : The file path to save the text output.
    
    append (boolean)     : If true, text output is appended to the file specified 
                           by savpath. If the file does not exist, it will be created.
    
    adjdoc (boolean)     : If true, an additional text file is produced with
                           information about which image adjustmenst were used.
    
    psm (int)            : Tesseract configuration for Page Segmentation Mode. 
                          https://github.com/tesseract-ocr/tesseract/blob/master/doc/tesseract.1.asc
                         
    oem (int)            : Tesseract configuration for OCR Engine mode. 
                          https://github.com/tesseract-ocr/tesseract/blob/master/doc/tesseract.1.asc 
    
    Returns
    --------------------------------------------------------------------------
    none
    
    """
    
    #if a filename is used for the image, load the image
    if type(img) == str:
        img = Image.open(img)
        
    # Set up tesseract config
    if 0 <= psm <= 13:
        pconfig = "--psm " + str(psm)
    else:
        return "Invalid tesseract config."
    
    if 0 <= oem <= 3:
        oconfig = "--oem " + str(oem)
    else:
        return "Invalid tesseract config."
    
    tconfig = pconfig + " " + oconfig

    #determine mode to open text file
    if append == True:
        mode = {"mode": "a"}
    else:
        mode = {"mode": "w"}
    
    #open file and perform ocr    
    ocrf = open(savpath, **mode)
    text = pytesseract.image_to_string(adjustImg(img, **kwargs), config = tconfig)
    ocrf.write(text.encode("utf-8", errors = "replace") + "\n\n")
    ocrf.close()
        
    #create the adjustments documentation file
    if adjdoc == True:
        dirpath = os.path.split(savpath)[0]
        adjf = open(os.path.normpath(os.path.join(dirpath, "_adjustments.txt", "w")))
        adjf.write("IMAGE ADJUSTMENTS\n\n")
        for key, value in kwargs.items():
            adjf.write("{}: {}\n" .format(key, value))
        adjf.close()
        
    return

def tsvOCR(img, savpath, tsvfile, p = 1, append = True, psm = 1, oem = 3):
    
    """
    
    Run OCR on an image and produce a TSV file along with text. Can limit which 
    files are added to the TSV by way of binomial sampling.
    
    Arguments
    --------------------------------------------------------------------------    
    img (str, PIL image) : Either the file path of an image or a PIL image object
    
    savpath (str)        : The file path to save the text output.
    
    tsvfile (str)        : Name of a TSV file that will be produced in the same 
                           directory as the text output. Ignored if not specified.

    p                    : Probability to use for binomial sampling. If 1, no sample
                           will be taken.                            

    append (boolean)     : If true, text output is appended to the file specified 
                           by savpath. If the file does not exist, it will be created.
                           Note: this argument also applies to the TSV output if a
                           TSV file is specified.
    
    psm (int)            : Tesseract configuration for Page Segmentation Mode. 
                          https://github.com/tesseract-ocr/tesseract/blob/master/doc/tesseract.1.asc
                         
    oem (int)            : Tesseract configuration for OCR Engine mode. 
                          https://github.com/tesseract-ocr/tesseract/blob/master/doc/tesseract.1.asc 
    
    Returns
    --------------------------------------------------------------------------
    none
    
    """
    
    #if a filename is used for the image, load the image
    if type(img) == str:
        name = os.path.split(img)[1]
        img = Image.open(img)
    else:
        name = img.info["name"]
        
    # Set up tesseract config
    if 0 <= psm <= 13:
        pconfig = "--psm " + str(psm)
    else:
        return "Invalid tesseract config."
    
    if 0 <= oem <= 3:
        oconfig = "--oem " + str(oem)
    else:
        return "Invalid tesseract config."
    
    tconfig = pconfig + " " + oconfig

    #determine mode to save files
    if append == True:
        mode = {"mode": "a"}
    else:
        mode = {"mode": "w"}
        
    #Get TSV data
    tsvs = pytesseract.image_to_data(img, config = tconfig)
    tdf = pandas.read_csv(StringIO(tsvs), 
                          sep = "\t", 
                          engine = "python",
                          error_bad_lines = False)

    #Turn TSV data into text
    par = 0
    line = 0
    text = ""
    
    for row in tdf.itertuples():
        token = str(row.text)

        #adjust tokens
        if token == "nan":
            continue
        if row.par_num != par:
            par = row.par_num
            line = row.line_num
            token = "\n\n" + token + " "
        elif row.line_num != line:
            line = row.line_num
            token = "\n" + token + " "
        else:
            token = token + " "
                    
        #compile text
        text = text + token
        
    #write text to file    
    ocrf = open(savpath, **mode)
    ocrf.write(text)
    ocrf.close()
    
    #Drop TSV columns we don't need
    tdf = tdf.drop(columns = ["level", "page_num", "block_num", "par_num", "line_num", "word_num"])

    #Sample TSV data    
    if p != 1:
        samp = random.binomial(size = tdf.count()[0], n = 1, p = p)
    
        r = 0
        for s in samp:
            if s == 0:
                tdf = tdf.drop(r)
            r += 1    
    
    #if we aren't left with an empty data frame
    if tdf.count()[0] != 0:
        
        #add a column for the image name
        tdf["name"] = name
        
        #determine if a header is needed
        dirpath = os.path.split(savpath)[0]
        if append == True and os.path.exists(os.path.normpath(os.path.join(dirpath, tsvfile))) == True:   
            header = False
        else:
            header = True
        
        #write data to TSV file
        tsvf = open(os.path.normpath(os.path.join(dirpath, tsvfile)), **mode)
        tdf.to_csv(tsvf, index = False, sep = "\t", header = header)
        tsvf.close()
    
    return

class testList():
    
    """
    
    testLists are used for testing the accuracy of OCR on a sample of images.
    
    The purpose of the testList class is to allow multiple iterations of image
    adujustments and compare the OCR accuracy when those adjustments are applied. 
    For example, a testList can help determine if OCR will perform better on a
    sample of grayscale images or a sample of color images.
    
    A testList object can be instantiated with a list of image file paths using 
    the mkOCRtestList function.    

    Attributes
    --------------------------------------------------------------------------    
    
    images (list)            : A list of PIL image objects.
    
    results (list)           : A list of dictionaries, each corresponding with
                               an image object in the images list. The 
                               dictionaries are records with information about 
                               OCR accuracy that have been returned by the 
                               OCRtestImg function.
    
    Methods
    --------------------------------------------------------------------------    
    
    adjustTest               : Test the results of image adjustments on OCR 
                               accuracy.
    
    adjustImg                : Applies image adjustments to all images in the
                               testList.
                               
    """
    
    def __init__(self, images, results):
        
        """
        
        Arguments
        -----------------------------------------------------------------------   
    
        images (list)         : A list of PIL image objects.
    
        results (list)        : A list of dictionaries, each corresponding with
                                an image object in the images list. The 
                                dictionaries are records with information about 
                                OCR accuracy that have been returned by the 
                                OCRtestImg function.
                                
        """
        
        self.images = images
        self.results = results
    
    
    def adjustTest(self, test, levels=[0,.25,.5,.75,1]):
        
        """
        
        Test the results of image adjustments on OCR accuracy.
        
        adjustTest can test any of the image adjustments available through the 
        adjustImg function. With boolean adjustments (such as invert), OCR
        accuracy information is provided for both True and False states. For
        continuous adjustments (such as brightness), the adjustments are tested
        at multiple levels supplied by the user.
        
        An adjustTest returns a dictionary with two items:
            
        The first item is a table that shows the number of unknown tokens for 
        each image at each level (or boolean state) along with the total 
        tokens for the image.
        
        The second item is a summary of total readability for all images at
        each level (or boolean state).
        
        Arguments
        --------------------------------------------------------------------------    
        
        test (str)              : An image adjustment to test. Can include any
                                  of the adjustments available through the 
                                  adjustImg function.
        
        levels (list)           : The levels at which a continuous adjustment
                                  will be tested. OCR accuracy information will 
                                  be returned for each image at each level. 
                                  Levels are ignored when boolean adjustments 
                                  are used.
                        
        Returns
        --------------------------------------------------------------------------
        (dict) The results of the test.
        
        """
        
        resultsT = {}                       #Results Table
        totaltok = []                       #Total tokens for each file
        rownum = 0                          #Row Number
        names = {}                          #dictionary for renaming row indices
        results = {}                        #dictionary with results to return
        readults = "\nTOTAL READABILITY"    #readability results to return
        topScore = 0                        #highest readability score
        topAdj = "none"                     #adjustment with the best readability
        state = True                        #Initial State for boolean tests
        
        #Distinguish between continuous and boolean tests
        conTests = ["color", "brightness", "contrast", "autocontrast", "sharpness"]
        boolTests = ["invert", "blur", "sharpen", "smooth", "xsmooth"]

        #Tests with continuous levels
        if test in conTests:
                        
            #build column for each level
            for level in levels:
                
                #create column header and start with empty column
                header = test + str(level)
                resultsC = []
                
                #loop through each sample image
                for img in (self.images): 
                    
                    #run image test, record unknown tokens
                    name = img.info["name"]
                    corImg = OCRtestImg(adjustImg(img, **{test: level}))
                    resultsC.append(len(corImg["unknown_words"]))
                    img.info = {"name" : name}
                    
                #add column to table    
                resultsT[header] = resultsC
                
        #Tests with boolean states
        elif test in boolTests:
    
            #build columns for each state
            for i in range (0,2):
                
                #Create column header and start with empty column
                header = test + str(state)
                resultsC = []
                
                #loop through each sample image
                for img in (self.images): 
                    
                    #run image test, record unknown tokens
                    name = img.info["name"]
                    corImg = OCRtestImg(adjustImg(img, **{test: state}))
                    resultsC.append(len(corImg["unknown_words"]))
                    img.info = {"name" : name}                    
                
                #add column to table    
                resultsT[header] = resultsC
                
                #change state
                state = False    
        
        #Unknown tests
        else:        
            return "Invalid image adjustment test."
        
        #get total tokens and filename
        for img in self.images:
            names[rownum] = img.info["name"]
            rownum += 1
        
        for res in self.results:
            totaltok.append(res["token_count"])

        #create table and rename rows
        resultsT["totaltok"] = totaltok
        resultsT = pandas.DataFrame(resultsT)
        resultsT = resultsT.rename(index = names)
        
        #calculate readability for each level          
        alltoks = resultsT["totaltok"].sum()

        for col in resultsT:
            total = 0
            if col != "totaltok":
                total = resultsT[col].sum()
                if total != 0:
                    readability = round(100 - ((float(total)/float(alltoks)) * 100), 3)
                else:
                    readability = 100
                readults = readults + "\n" + col + ": " + str(readability)
                if readability > topScore:
                    topScore = readability
                    topAdj = col
        
        #return results
        results = {
        "table" : resultsT,
        "readability" : readults,
        "best_adjustment": topAdj
        }
        
        print ("\n\n")
        print (results["table"])
        print (results["readability"])
        
        return results


    def adjustSampleImgs(self, **kwargs):
        
        """
        
        Applies image adjustments to all images in the testList.
        
        Once image adjustments have been tested on the sample of images in the
        testList, a user may wish to apply an adjustment permanently in 
        order to continue testing combinations of adjustments. This process 
        supports a "layering" of adjustments in order to obtain the best OCR 
        results on a given set of images.
        
        When adjustSampleImgs is used on a testList, OCRtestImg is also applied to the
        new image objects and a new testList object is returned.
        
        Arguments
        --------------------------------------------------------------------------    
        
        **kwargs              : keyword arguments are passed to the 
                                adjustImg function.
        
        Returns
        --------------------------------------------------------------------------
        A testList object.
        
        """
        
        #Create empty lists for storing the new images and records
        newimgs = []
        newresults = []
        
        #Apply image adjustment to all images and get new OCR test results
        for img in self.images:
            name = img.info["name"]
            img = adjustImg(img, **kwargs)
            img.info = {"name" : name}
            newimgs.append(img)
            newresults.append(OCRtestImg(img))
        
        #Return a new testList object
        testObj = testList(newimgs, newresults)
        return(testObj)