# -*- coding: utf-8 -*-
"""
Created on Fri Aug  7 11:23:54 2020

@summary: Creates two corpus-level report files on remaining section errors 
    to aid in future error correction efforts. The first 
    ('remaining_sec_errors.csv') consists of volume-level information about 
    remaining section gaps. The second ('final_error_chap_rows.csv') contains 
    section-level information for all chapters containing section numbering 
    errors, as identified by section numbering 'gaps'. In the Split Cleanup 
    Jupyter notebook, this script corresponds to "Step 8. Generating Final 
    Files / Remaining Error Appraisal".


@author: Neil Byers

Digital Research Services
University Libraries
UNC Chapel Hill
"""


import csv
import pandas as pd
import os
from string import punctuation
import numpy as np
import joblib
csv.field_size_limit(600000)


def error_check(raw_file):
    """    
    This function compiles information related to the section 'gaps' present in
    a single volume. This information (total sections, chapters containing errors,
    types of errors remaining, etc.) is then used to compile two corpus-level
    report files to aid in future rounds of manual review. One, the 'meta' section
    errors file, contains metadata related to the remaining errors (gaps) in each
    volume of the corpus. The second, 'final_error_chap_rows.csv' consists of 
    rows for all sections of all chapters in the corpus which still contain
    sections preceded by 'gaps' after all of the previous cleanup steps. These
    files will be used in future rounds of manual and automatic review to complete
    the section cleanup process for the entire corpus.
    
    Arguments
    --------------------------------------------------------------------------    
    raw_file (str)           : The "raw" file path for a single volume

    Returns
    --------------------------------------------------------------------------
    report_row               : A dictionary containing the title of the volume,
                               the total number sections, the total number of 
                               chapters, the number of remaining section errors,
                               the number of chapters containing section errors,
                               and a list of dictionaries, one for each section,
                               for all sections in chapters that still contain
                               sections with 'gaps'.
    """
    
    # Read in raw file
    raw_df = pd.read_csv(raw_file, encoding='utf-8', low_memory=False)

    # eliminate np.nan from the raw dataframe
    raw_df['chapter'] = raw_df['chapter'].replace(np.nan, '')
    raw_df['section'] = raw_df['section'].replace(np.nan, '')
    raw_df['text'] = raw_df['text'].replace(np.nan, '')

    #reset chapter_index
    raw_df["chapter_index"] = (raw_df.chapter != raw_df.chapter.shift(1)).cumsum()
    raw_df['chapter_index'] = raw_df['chapter_index'].replace(np.nan, '')

    #Reset section index
    raw_df["section_index"] = (raw_df.section != raw_df.section.shift(1)).groupby(raw_df.chapter).cumsum()  





    # Create a dataframe for the volume's sections, one per row
    sections = raw_df.loc[:, ['chapter', 'chapter_index', 'section', 'section_index']].drop_duplicates()
    # Extract the numeric values from the section headers and convert them to float
    sections['raw_num'] = sections['section'].apply(lambda x: 0 if x == "Chapter_Title" else (x.strip().split()[1].rstrip(punctuation) if " " in x.strip() and x.strip().split()[1].rstrip(punctuation).isnumeric() else np.nan))
    sections.loc[sections["section"]=="Paratextual", "raw_num"] = 0
    sections['raw_num'] = sections['raw_num'].astype(float)
    
    # Create a groupby dataframe to group the sections by their respective chapters
    chapters = sections.groupby('chapter_index')

    # Generate the gap information for each section
    # This value indicates the numeric distance between a given section number
    # and that of the preceding section
    sections["gap"] = chapters.raw_num.diff(1)
    sections["gap"] = sections["gap"].replace(np.nan, 1)



    # Create a list of the unique gap values present in the volume
    gaps_remaining = sections['gap'].value_counts().keys().tolist()
    # Determine the frequencies of the above gap values
    gap_counts = sections['gap'].value_counts().tolist()

    # Create variables for frequencies of gaps of 2, gaps of 3, and gaps of any
    # other value with the exception of 1
    two_gaps_left = 0
    three_gaps_left = 0
    other_gaps_left = 0

    for i in range(0, len(gaps_remaining)):
        if gaps_remaining[i] == 2:
            two_gaps_left = gap_counts[i]
        elif gaps_remaining[i] == 3:
            three_gaps_left = gap_counts[i]
        elif gaps_remaining[i] != 1:
            other_gaps_left += gap_counts[i]


    # Calculate total sections in the volume, including those that are missing
    # "Other" gaps are excluded because these are often not actual gaps and
    # are likely to artificially inflate the section count variable.
    total_sections = sections.shape[0]+two_gaps_left+(2*three_gaps_left)
    total_chapters = len(chapters.groups.keys())

    # Calculate 'errors remaining' to include missing chapters and 'other' errors,
    # as indicated by gaps with values other than 1, 2, or 3.
    errors_remaining = two_gaps_left+(2*three_gaps_left)+other_gaps_left
    
    # Extract the volume title
    vol = os.path.basename(raw_file).replace("_data_cleaned_new.csv", "")



    # Create a dataframe that includes all sections for all chapters containing
    # sections with a gap value other than one, or zero in the case of Paratextuals
    # and Chapter_Titles
    error_chaps = []
    total_error_chaps = 0
    for b in chapters.groups.keys():
            chap_sects = chapters.get_group(b)
            for r in range(0,chap_sects.shape[0]):
                if (chap_sects.iloc[r]['gap']==0 and chap_sects.iloc[r]['section_index']!=1) or chap_sects.iloc[r]['gap']!=1:
                    total_error_chaps += 1
                    for b in range(0,chap_sects.shape[0]):
                        error_chaps.append({"vol":vol, 
                                                 "ch_index":chap_sects.iloc[b]['chapter_index'], 
                                                 "ch_title":chap_sects.iloc[b]['chapter'],
                                                 "sec_index":chap_sects.iloc[b]['section_index'],
                                                 "sec_title":chap_sects.iloc[b]['section'],
                                                 "gap":chap_sects.iloc[b]['gap']})
                    break


    # Compile the data below into a dictionary. This dictionary is then returned
    # by the function to be added as a row to a corpus-level report. Rows from
    # the 'error_chaps' list will be added to a corpus-level document containing
    # all sections of all chapters containing sections with remaining gaps
    report_row = {"vol":vol,
                  "total_chapters":total_chapters,
                  "total_sections":total_sections,
                  "errors_remaining":errors_remaining,
                  "error_chaps": total_error_chaps,
                  "error_chaps_list": error_chaps}

    return report_row


def main():
    
    # Set raw file directory variables and create a list of all raw files
    raw_path = r"C:\Users\npbyers\Desktop\OTB\SectNumFixes\final\raw"   
    rawfolder = "./final/raw/"    
    raw_filelist = [(rawfolder + f) for f in os.listdir(raw_path) if f.endswith(".csv")]

    
    # Call the error_check function above, once for each volume, in parallel
    # to decrease compute time.
    with joblib.parallel_backend(n_jobs=7,backend='loky'):
        report_rows = joblib.Parallel(verbose=5)(
        joblib.delayed(error_check)(raw_file) for raw_file in raw_filelist)
    
    # Compile the .csv file with all sections from all chapters containing
    # sections with unusual gaps (gaps with values other than 1, or 0 in 
    # certain cases)
    error_chap_master = []    
    for row in report_rows:
        for i in row['error_chaps_list']:
            error_chap_master.append(i)    
    error_chap_df=pd.DataFrame(error_chap_master)
    error_chap_df.to_csv(r"C:\Users\npbyers\Desktop\OTB\SectNumFixes\final_error_chap_rows.csv", index=False)
    
    # Compile the .csv file with volume-level information about remaining errors
    # in the corpus as whole.
    report_df = pd.DataFrame(report_rows)   
    meta_df = report_df.drop('error_chaps_list', 1)    
    meta_df.to_csv(r"C:\Users\npbyers\Desktop\OTB\SectNumFixes\remaining_sec_errors.csv", index=False)


if __name__ == "__main__":
    main()