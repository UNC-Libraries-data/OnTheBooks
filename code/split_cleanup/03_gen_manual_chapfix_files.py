# -*- coding: utf-8 -*-
"""
Created on Fri Aug  7 08:44:09 2020

@summary: This script creates the files used in "Step 5. Chapter Cleanup: 
    Second Manual Pass" (see the Split Cleanup Juypter notebook). These
    files, called 'flag_rows' files, consist of all rows from a given volume's 
    raw file which belong to chapters that remain 'flagged' - in other words, 
    those chapters in the volume that are identified as being in the vicinity 
    of chapter numbering errors. It places these new files along with the 
    'chapnumflags' files from previous steps in volume-specific directories to
    enable quick action by manual reviewers.


@author: Neil Byers

Digital Research Services
University Libraries
UNC Chapel Hill
"""


import pandas as pd
import os
import numpy as np
import joblib
import shutil

def create_manual_files(raw_fix_pair):
    """    
    This function generates files containing only those rows in a raw file
    that belong to chapters which remain 'flagged' after the first rounds of 
    manual and automatic chapter numbering error corrections. One "flag_rows"
    file is generated for each volume with remaining chapter errors. These files
    are intended by use for manual reviewers to aid them in cleaning the chapter 
    errors that could not be fixed automatically.
    
    The "flag_rows" files contain chapter, section, text, and chapter_index 
    information for each row (word). Volume metadata and Internet Archive
    jpeg/pdf urls for each page are also included. These final piees of information
    allow for manual reviewers to quickly access page images to aid in them
    in correcting errors. Finally, the raw file index location for each row is 
    added so that any changes made to the "flag_rows" file can be be re-integrated
    into new versions of the raw files.
    
    Once the "flag_rows" file is compiled, it is output as a .csv file. A version 
    of the final 'chapnumfixes' file for each affected volume is copied into the 
    same directory so that manual reviewers will have access to all necessary
    files in one location.
    
    Arguments
    --------------------------------------------------------------------------    
    raw_fix_pair (list)         : List with the string filepaths for both the 
                                  raw file and "chapnumfixes" file for a 
                                  given volume.

    Returns
    --------------------------------------------------------------------------
    N/A
    """
    
    # load files & create dataframes

    rawfile = raw_fix_pair[0]
    fixfile = raw_fix_pair[1]
    volume = (os.path.basename(rawfile))
    volume = volume.replace("_output_chapadjusted_rd2.csv", "")

    raw_df = pd.read_csv(rawfile, encoding='utf-8', low_memory=False)
    fix_df = pd.read_excel(fixfile, encoding='utf-8')

    # Identify raw file rows assigned to "flagged" chapters and compile a new
    # dataframe containing only these rows.
    if (fix_df['flag']==True).any():

        raw_df['chapter'] = raw_df['chapter'].replace(np.nan, '')
        raw_df['section'] = raw_df['section'].replace(np.nan, '')
        raw_df['text'] = raw_df['text'].replace(np.nan, '')
        raw_df['chapter_index'] = raw_df['chapter_index'].replace(np.nan, '')
        raw_df['flag'] = False

        for i in range(0, fix_df.shape[0]):
            idx = fix_df.iloc[i]["chapter_index"]
            if fix_df.iloc[i]['flag']:
                raw_df.loc[((raw_df["chapter_index"]==idx)), ["flag"]] = True

        flag_df = raw_df[raw_df['flag']==True].copy()

        # Add IA urls to flag_rows file
        flag_df["vol"] = flag_df["name"].str.split(pat = "_")
        flag_df["vol"] = flag_df["vol"].apply(lambda x: x[0])
        flag_df['img_num'] = flag_df["name"].str.split(pat = "_")
        flag_df['img_num'] = flag_df['img_num'].apply(lambda x: x[1].replace(".jp2", ""))
        flag_df["jpg_url"] = "https://archive.org/download/" + flag_df["vol"] + "/" + flag_df["vol"] + "_jp2.zip/" + flag_df["vol"] + "_jp2%2F" + flag_df["name"] + "&ext=jpg"
        flag_df["pdf_url"] = "https://archive.org/download/" + flag_df["vol"] + "/" + flag_df["vol"] + ".pdf#page=" + flag_df['img_num']


        flag_df = flag_df[['text', 'name', 'chapter', 'section', 'jpg_url', 'pdf_url']]


        # Output flag_rows file
        # Copy the chapnumfixes file to the same location
        outname = volume + "_flag_rows.csv"

        outdir = "./manual_fixes/" + volume
        if not os.path.exists(outdir):
            os.mkdir(outdir)

        fullname = os.path.join(outdir, outname)

        flag_df.to_csv(fullname, index_label="rawfile_index")
        shutil.copy2(fixfile, outdir)
        
def main():
    # Set directories for raw and "chapnumfixe" files
    raw_path = r"C:\Users\npbyers\Desktop\OTB\ChapNumFixes\chap_adjusted_raw_round2"
    fix_path = r"C:\Users\npbyers\Desktop\OTB\ChapNumFixes\chap_num_fixes_final"
    
    rawfolder = "./chap_adjusted_raw_round2/"
    fixfolder = "./chap_num_fixes_final/"
    
    # Create filepath lists for both sets of files
    raw_filelist = [(rawfolder + f) for f in os.listdir(raw_path) if f.endswith(".csv")]
    fix_filelist = [(fixfolder + f) for f in os.listdir(fix_path) if f.endswith(".xlsx")]

    # Create a list of pairs, each containing the path for a raw file
    # and "chapnumfixes" file for a given volume
    raw_fix_pairs = []
    for i in range(0, len(raw_filelist)):
        raw_fix_pairs.append([raw_filelist[i], fix_filelist[i]])
    
    # Run the 'create_manual_files' function in parallel to reduce compute time
    with joblib.parallel_backend(n_jobs=7,backend='loky'):
        joblib.Parallel(verbose=5)(joblib.delayed(create_manual_files)(pair) for pair in raw_fix_pairs)


if __name__ == "__main__":
    main()