#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri May 31 16:46:58 2019

@author: Lorin Bruckner

Digital Research Services
University Libraries
UNC Chapel Hill
"""

import pandas as pandas
from nltk import word_tokenize

#Read in the tab delimited file from http://download.geonames.org/export/dump/US.zip
#File was downloaded 5/31/19, 4:41 PM
gn = pandas.read_csv("/Users/tuesday/Documents/_Projects/Research/OnTheBooks/US/US.txt", sep ="\t", header = None)

#Filter records for North Carolina 
ncgn = gn[gn.loc[:,10] == "NC"]

#Dump all geonames into a single string
geonames = ""
for index,row in ncgn.iterrows():
    if type(row[2]) is str: 
        geonames = geonames + " " + row[2]

#Tokenize geonames. Remove punctuation, duplicates and single letters. Make lowercase.
geotokens = word_tokenize(geonames)
geotokens = [token for token in geotokens if token.isalpha()]
geotokens = list(dict.fromkeys(geotokens))
geotokens = [token for token in geotokens if len(token) > 1]
geotokens = [token.lower() for token in geotokens]

#Create text file to add to Spell Checker
with open("/Users/tuesday/Documents/_Projects/Research/OnTheBooks/geonames.txt", "w") as file:
    for token in geotokens:
        file.write(token + " ")