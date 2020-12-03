#!/usr/bin/env python
# coding: utf-8

"""
jp2_download.py

    
@summary: This script downloads and stores volumes of image files from
    the Internet Archive. It uses an existing list of volume
    titles to create request links.
    
    Once the downloads are complete, the script checks for errors.
    
    It uses the volume title list mentioned above to check for missing
    volumes so that the user can download missing volumes manually. 
    It then checks for download errors by comparing file sizes
    of local copies with those of the Internet Archive copies.
    
    Discrepancies are printed for the user.

@author: Rucha Dalwadi

Digital Research Services
University Libraries
UNC Chapel Hill

"""

import urllib.request
import os
import csv
import time

os.chdir(r"")# The Directory where you want the pdfs to be downloaded in like C:\Users\onthebooks\Documents\lawpdfs

# Open the file with identifiers for parsing
with open("search.csv","r") as identifiers:
    reader=csv.DictReader(identifiers)
    l=[d['identifier'] for d in reader] # identifier is the column with the volume names

ct=0
start=time.time()
problems=list()
fails=0
sourcelink = 'https://archive.org/download/'  # A single web source contains all the files to download

# The identifiers are used to generate links to the images for download
for f in l:
    try:
        ct+=1
        # A download link is created for each file by appending the id and file extension to the source
        full_link = sourcelink+f+'/'+f+'_jp2.zip'         
        urllib.request.urlretrieve(full_link, f+'_jp2.zip')
        time.sleep(120)
        if ct%10==0:
            print(str(ct)+": "+f)
            print(time.time()-start)
    except:
        fails+=1
        time.sleep(60)

end=time.time() 
print(end-start)

## Checking for and resolving problems:

for f in l:
    zips= sourcelink + f +'/' +f+ '_jp2.zip'
    
# Get a list of the missing folders
missed=[f for f in zips if f.split("/")[-1] not in os.listdir(".")]
print(missed)
#manually download missed files

# Get a list of the items with broken links by comparing file sizes of the
# original file to the downloaded file
broken_dl=[]
for z in zips:
    local=z.split("/")[-1]
    local_size=os.path.getsize(local)
    with urllib.request.urlopen(z) as web:
        meta=dict(web.info())
        web_size=int(meta["Content-Length"])
    if web_size!=local_size:
        broken_dl.append(z)

# Print the sizes of the broken files and original files for comparison
for z in broken_dl:
    local=z.split("/")[-1]
    local_size=os.path.getsize(local)
    with urllib.request.urlopen(z) as web:
        meta=dict(web.info())
        web_size=int(meta["Content-Length"])
    print(local_size/(1024^2),web_size/(1024^2))

