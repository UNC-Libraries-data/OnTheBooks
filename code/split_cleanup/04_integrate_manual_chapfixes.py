# -*- coding: utf-8 -*-
"""
Created on Fri Aug  7 09:28:51 2020

@summary: This script integrates the changes made as part of
    "Step 5. Chapter Cleanup: Second Manual Pass" 
    (see the Split Cleanup Juypter notebook) to the corpus raw files. It does
    so first by integrating changes made by manual reviewers to the 'flag_rows' 
    files (created by 'gen_manual_chapfix_files.py') back into their
    respective raw files. Following this operation, transcriptions made by
    manual reviewers are inserted as new rows into the raw files. This step
    concludes the chapter cleanup operations and generates a new round of
    aggregate and raw files for use in the following section cleanup process.

@author: Neil Byers

Digital Research Services
University Libraries
UNC Chapel Hill
"""


import csv
import pandas as pd
import joblib
import os
import numpy as np
from shutil import copyfile
csv.field_size_limit(600000)



def insert_tr_rows(insertion_idx, joined, transcribed_rows):
    """    
    This function inserts new raw file rows created from transcribed text
    into an existing raw file
    
    Arguments
    --------------------------------------------------------------------------    
    insertion_idx (int)                    : The original raw file index 
                                             at which the new rows are to 
                                             be inserted
                                  
    joined (pandas.DataFrame)              : The new version of the raw 
                                             dataframe with "flag_rows" file 
                                             edits and previous transcription 
                                             insertions included
                                  
    transcribed_rows (pandas.DataFrame)    : A dataframe with rows
                                             from transcribed text.
    Returns
    --------------------------------------------------------------------------
    N/A
    """
    
    # Set the point at which the dataframe will be split
    row_number = insertion_idx+1
    
    # Store the upper half of the original dataframe
    df1 = joined[0:row_number] 
   
    # Store the lower half of the original dataframe
    df2 = joined[row_number:] 
   
    # Concat the upper half, the newly transcribed rows, and the lower half
    df_result = pd.concat([df1, transcribed_rows, df2]) 
   
    # Reassign the index labels 
    df_result.index = [*range(df_result.shape[0])] 
   
    # Return the updated dataframe 
    return df_result 



def fix_integration(fix_dict):
    """    
    This function adds all changes made in the flag_rows files to new versions
    of the raw files. It then inserts all text transcribed by manual reviewers
    as new rows in the raw file. It then outputs .csv versions of the new raw
    and aggregate files.
    
    Arguments
    --------------------------------------------------------------------------    
    fix_dict (dict)         : Contains filepaths for both the raw ('raw' - str)
                              and flag_rows ('flag_rows' - str) files as well as
                              the rows in the corpus-level manual fix file that
                              relate to the volume in question
                              ('fixes' - pandas.DataFrame)
    Returns
    --------------------------------------------------------------------------
    N/A
    """    
    
    # build/prep the three necessary dataframes from a given volume.
    # fix_dict contains:
    # 1. The path to the old raw file
    # 2. The path to the flag_rows file
    # 3. A slice of the fixes file with only the rows pertaining to that volume
    raw_file = fix_dict['raw']
    flag_rows_file = fix_dict['flag_rows']
    fix_df = fix_dict['fixes']
    raw_df = pd.read_csv(raw_file, encoding='utf-8', low_memory=False)
    flag_rows_df = pd.read_csv(flag_rows_file, encoding='utf-8', low_memory=False)

    fix_df['transcription_ID'] = fix_df['transcription_ID'].replace(np.nan, '')
    fix_df['transcription_index'] = fix_df['transcription_index'].replace(np.nan, '')

    flag_rows_df['text'] = flag_rows_df['text'].replace(np.nan, '')
    flag_rows_df['transcribed'] = flag_rows_df['transcribed'].replace(np.nan, '')
    flag_rows_df.columns = ["rawfile_index", "fr_text", "fr_name", "fr_chapter", "fr_section", "transcribed", "jpg_url", "pdf_url"]
    flag_rows_df.set_index('rawfile_index', inplace=True)


    raw_df['chapter'] = raw_df['chapter'].replace(np.nan, '')
    raw_df['section'] = raw_df['section'].replace(np.nan, '')
    raw_df['text'] = raw_df['text'].replace(np.nan, '')
    raw_df['chapter_index'] = raw_df['chapter_index'].replace(np.nan, '')
    
    # Apply flag_row file changes to raw file
    joined = raw_df.join(flag_rows_df)
    joined['fr_name'] = joined['fr_name'].replace(np.nan, 'NON_FLAG_ROW')
    joined.loc[(joined['fr_name']!="NON_FLAG_ROW"), ["chapter"]] = joined['fr_chapter']
    joined.loc[(joined['fr_name']!="NON_FLAG_ROW"), ["text"]] = joined['fr_text']
    joined.loc[(joined['fr_name']!="NON_FLAG_ROW"), ["section"]] = joined['fr_section']

    # Remove extraneous columns leftover from flag_rows join
    del joined["fr_text"]
    del joined["fr_name"]
    del joined["fr_chapter"]
    del joined["fr_section"]
    del joined["transcribed"]
    del joined["jpg_url"]
    del joined["pdf_url"]
    
    # make a list of the unique transcription IDs so groups of multiple 
    # transcribed chapters/transcriptions can be inserted into the new raw 
    # dataframe in blocks
    transcriptions = [i for i in list(fix_df.transcription_ID.unique()) if i != '']

    # Add markers at each index that requires a transcription directly beneath it BEFORE
    # any transcribed rows are added. That way the new rows can be added based on the markers
    # and not based on indices that will change with each insertion.
    transcription_ID_idx_pairs = fix_df.loc[:, ['transcription_index', 'transcription_ID']].copy().drop_duplicates()
    transcription_ID_idx_pairs = transcription_ID_idx_pairs[transcription_ID_idx_pairs['transcription_index']!='']
    joined['transcription_here'] = ""
    for idx, row in transcription_ID_idx_pairs.iterrows():
        insert_idx = row['transcription_index']
        joined.loc[insert_idx, ['transcription_here']] = row['transcription_ID']

        
        
    # Insert transcribed text into the new version of the raw file. Transcribed
    # text strings are split into a dataframe with a row for each word. This new
    # transcribed dataframe is then inserted into the raw file using the 
    # 'insert_tr_rows' function     
    for t in transcriptions:
        insertion_idx = joined.index[joined['transcription_here']==t][0]
        rows = []
        for i in range(0, fix_df.shape[0]):
            if fix_df.iloc[i]['transcription_ID']==t:

                #reconstruct image name
                vol_name = fix_df.iloc[i]['Volume']
                vol_base = vol_name[:vol_name.find("_")+1]
                img_url = fix_df.iloc[i]['Affected image jpg url']
                img_num=img_url[img_url.rfind("_")+1:].replace('.jp2&ext=jpg', '')
                img_name = vol_base+img_num+".jp2"

                chap = fix_df.iloc[i]['transcription_chapter']
                sec = fix_df.iloc[i]['transcription_section']
                text = fix_df.iloc[i]['transcription_text']
                word_list = text.split()
                for word in word_list:
                    rows.append({"left":"", 
                                  "top":"", 
                                  "width":"", 
                                  "height":"", 
                                  "conf":100, 
                                  "text":word, 
                                  "name":img_name, 
                                  "chapter":chap, 
                                  "section":sec, 
                                  "chapter_index":""})

        transcribed_rows = pd.DataFrame(rows)

        joined = insert_tr_rows(insertion_idx, joined, transcribed_rows)
    
    # reset the chapter indices
    joined["chapter_index"] = ((joined["chapter"]!="") & ((joined["chapter"]!=joined["chapter"].shift(1)) | ((joined["section"] == "Chapter_Title") & (joined["section"]!=joined["section"].shift(1))))).cumsum()
    
    #create new agg file
    agg = joined[joined["text"]!=""].groupby(['chapter', 'section', 'chapter_index'], sort=False)['text'].apply(' '.join).reset_index()

    #output new raw and agg files to .csv
    raw_outname = raw_file.replace("_output_chapadjusted_rd2.csv", "_cleaned.csv")
    raw_outname = raw_outname.replace("/chap_adjusted_raw_round2/", "/chap_cleaned_new/raw/")
    agg_outname = raw_file.replace("_output_chapadjusted_rd2.csv", "_aggregated_cleaned.csv")
    agg_outname = agg_outname.replace("/chap_adjusted_raw_round2/", "/chap_cleaned_new/agg/")

    #output new raw/agg to file
    joined.to_csv(raw_outname, index=False, encoding="utf-8")
    agg.to_csv(agg_outname, index=False, encoding="utf-8")


def main():
    
    # Set directory locations for old and new raw/aggregate files
    raw_path = r"C:\Users\npbyers\Desktop\OTB\ChapNumFixes\chap_adjusted_raw_round2"
    manual_path = "./fix_mats/"
    
    rawfolder = "./chap_adjusted_raw_round2/"
    aggfolder = "./chap_adjusted_agg_round2/"
    
    rawfolder_new = "./chap_cleaned/raw/"
    aggfolder_new = "./chap_cleaned/agg/"
    
    # Initialize lists for each file type
    flag_rows_filelist = []
    vol_list = []
    raw_filelist = []
    
    # Create a list of flag_rows files and a list of volumes for
    # which flag_rows files exist
    for root, dirs, files in os.walk(manual_path):  
        for file in files:
            if "flag_rows" in file:
                folder = file.replace("_flag_rows.csv", "")
                flag_rows_filelist.append(manual_path + "/" + folder + "/" + file)
                vol_list.append(folder)
    
    # Create a list of all old raw files
    all_raw = [f for f in os.listdir(raw_path) if f.endswith(".csv")]
    
    # Create a list of raw files for those volumes with corresponding flag_rows
    # files. These are the raw files that will be sent to the 'fix_integration'
    # function.
    # If a volume did not undergo any manual fixes (and for which there is thus
    # no corresponding flag_rows file), the existing raw/agg files for that 
    # volume are simply copied and pasted to the new "chap_cleaned" destination
    # directory.
    for i in all_raw:
        base = i.replace("_output_chapadjusted_rd2.csv", "")
        raw_outname_new = i.replace("_output_chapadjusted_rd2.csv", "_cleaned.csv")
        agg_outname_new = i.replace("_output_chapadjusted_rd2.csv", "_aggregated_cleaned.csv")
        agg_inname_old = i.replace("_output_chapadjusted_rd2.csv", "_aggregated_chapadjusted_rd2.csv")
        if base in vol_list:
            raw_filelist.append(rawfolder+i)
        else:
            copyfile(rawfolder+i, rawfolder_new+raw_outname_new)
            copyfile(aggfolder+agg_inname_old, aggfolder_new+agg_outname_new)
            
            
            
    # Create a dataframe from the file in which all manual fixes and 
    # transcriptions from the previous step (manual review) have been recorded
    fixfile = r"C:\Users\npbyers\Desktop\OTB\ChapNumFixes\fix_mats\Chap_Error_Fixes_for_script.csv"
    fix_df = pd.read_csv(fixfile, encoding='utf-8', low_memory=False)
    
    
    # Extract the rows in the fix file that pertain to the volume in question
    # and add them as a new dataframe to a dictionary which also contains
    # the filepath strings for the raw and flag_rows files for that volume
    raw_flag_fix_dicts = []
    for i in range(0, len(raw_filelist)):
        vol_fix_df = fix_df[fix_df['Volume']==vol_list[i]].copy().reset_index()
        raw_flag_fix_dicts.append({'raw':raw_filelist[i], 'flag_rows':flag_rows_filelist[i], 'fixes':vol_fix_df})
        
        
    # Call the 'fix_integration' function using the dictionaries created above,
    # one for each volume with manual fixes to be integrated. This operation
    # is run in parallel to reduce compute time.
    with joblib.parallel_backend(n_jobs=7,backend='loky'):
        joblib.Parallel(verbose=5)(joblib.delayed(fix_integration)(fix_dict) for fix_dict in raw_flag_fix_dicts)
        
        
if __name__ == "__main__":
    main()