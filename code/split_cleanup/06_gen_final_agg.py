# -*- coding: utf-8 -*-
"""
Created on Fri Aug  7 10:44:11 2020

@summary: This script generates a final round of aggregate files from the raw 
    files that resulted from the automatic and manual section-cleaning 
    processes. In the Split Cleanup Jupyter notebook, this script corresponds
    to "Step 8. Generating Final Files / Remaining Error Appraisal"

@author: Neil Byers

Digital Research Services
University Libraries
UNC Chapel Hill
"""


import csv
import pandas as pd
import os
import numpy as np
import joblib
csv.field_size_limit(600000)


def generate_new(raw_file):
    """    
    This function generates new aggregate files to reflect changes made in the
    manual section error correction process. The final versions of these files
    contain 
    
    Arguments
    --------------------------------------------------------------------------    
    raw_file (str)           : The "raw" file path for a single volume

    Returns
    --------------------------------------------------------------------------
    N/A
    """

    raw_df = pd.read_csv(raw_file, encoding='utf-8', low_memory=False)

    raw_df['chapter'] = raw_df['chapter'].replace(np.nan, '')
    raw_df['section'] = raw_df['section'].replace(np.nan, '')
    raw_df['text'] = raw_df['text'].replace(np.nan, '')

    # reset chapter_index in raw files
    raw_df["chapter_index"] = (raw_df.chapter != raw_df.chapter.shift(1)).cumsum()
    raw_df['chapter_index'] = raw_df['chapter_index'].replace(np.nan, '')
    
    # reset section_index in raw files
    raw_df["section_index"] = (raw_df.section != raw_df.section.shift(1)).groupby(raw_df.chapter).cumsum()

    # Create a new aggregate dataframe with the jpeg image name on which
    # a given section begins included on each row (section)
    group_list = ['chapter', 'chapter_index', 'section', 'section_index']
    agg_dict = {'text': ' '.join,
                'name': 'first'}
    agg = raw_df[raw_df["text"]!=""].groupby(group_list, sort=False, as_index=False).agg(agg_dict)
    agg.rename(columns={"name":"first_jpeg"}, inplace=True)

    # Generate the Internet Archive jpeg/pdf urls for each section's start page
    # based on the page image file name. Each row (section) in the 
    # aggregate file will thus be paired with its page image urls
    agg["vol"] = agg["first_jpeg"].str.split(pat = "_")
    agg["vol"] = agg["vol"].apply(lambda x: x[0])
    agg['img_num'] = agg["first_jpeg"].str.split(pat = "_")
    agg['img_num'] = agg['img_num'].apply(lambda x: x[1].replace(".jp2", ""))
    agg["first_jpg_url"] = "https://archive.org/download/" + agg["vol"] + "/" + agg["vol"] + "_jp2.zip/" + agg["vol"] + "_jp2%2F" + agg["first_jpeg"] + "&ext=jpg"
    agg["pdf_url"] = "https://archive.org/download/" + agg["vol"] + "/" + agg["vol"] + ".pdf#page=" + agg['img_num']
    
    


    # Remove extraneous columns from aggregate dataframe
    agg = agg.drop(columns=['first_jpeg', 'vol', 'img_num'])

    #output new raw and agg files to .csv
    raw_outname = raw_file.replace("_output.csv", "_output_final.csv")
    raw_outname = raw_outname.replace("/sec_clean/raw1/", "/sec_clean_final/raw/")
    agg_outname = raw_file.replace("_output.csv", "_aggregated_output_final.csv")
    agg_outname = agg_outname.replace("/sec_clean/raw1/", "/sec_clean_final/agg/")


    #output new raw/agg to file
    raw_df.to_csv(raw_outname, index=False, encoding="utf-8")
    agg.to_csv(agg_outname, index=False, encoding="utf-8")
        
def main():
    # Set directory path locations for raw files
    raw_path = r"C:\Users\npbyers\Desktop\OTB\SectNumFixes\sec_clean\raw1"
    rawfolder = "./sec_clean/raw1/"
    
    # Create a list of all raw files
    raw_filelist = [(rawfolder + f) for f in os.listdir(raw_path) if f.endswith(".csv")]
    
    # Create a new aggregate file using the 'generate_new' function.
    # This operation is run in parallel to reduce compute time.
    with joblib.parallel_backend(n_jobs=7,backend='loky'):
        joblib.Parallel(verbose=5)(joblib.delayed(generate_new)(raw_file) for raw_file in raw_filelist)

if __name__ == "__main__":
    main()