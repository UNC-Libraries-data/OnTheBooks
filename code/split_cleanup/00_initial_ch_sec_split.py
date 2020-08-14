# -*- coding: utf-8 -*-
"""
Created on Tue Aug 11 14:14:58 2020

@summary: This script parses raw OCR output files for section and chapter
    headers. It creates new versions of these raw files as well as new files 
    that have been aggregated into sections. This script corresponds to the
    "Step 1. Initial Splitting Process" section of the Split Cleanup Jupyter 
    notebook.

@author: Rucha Dalwadi & Matt Jansen

Digital Research Services
University Libraries
UNC Chapel Hill
"""


import pandas as pd
import numpy as np
import joblib
import re
import os



def tsvparser(filename):
    """
    
    Identifies chapters and sections within a raw OCR output .tsv file for
    a single volume.
    
    Assigns chapter and section identifiers to rows in the raw file and
    creates an aggregate pd.DataFrame object grouping text into 
    individual sections.
    
    Outputs a new .csv version of the raw file and creates an initial .csv
    version of the aggregate file.
    
    Arguments
    --------------------------------------------------------------------------    
    filepath (str)       : The filepath for a single volume's raw .tsv OCR
                           output file.
                         
    
    Returns
    --------------------------------------------------------------------------
    N/A
    
    """


    
    # Import the raw .tsv file into a pd.DataFrame object
    raw=pd.read_csv(filename)
    raw['text'] = raw['text'].replace(np.nan, '')

    # Add columns to dataframe and create lists to which identified chapter
    # and section headers will be appended
    # Set the variables for chapter and section that will be used to fill out
    # the above lists
    chapter = '' 
    chapter_column = []
    raw['chapter'] = ''
    section = ''
    section_column = []
    raw['section'] = ''

    # Iterate through all rows in the raw file (word by word)
    for i in range(0, raw.shape[0]):
        
        # Initialize as variables the regex patterns used to identify 
        # chapters (match_chapter), abbreviate section headers 
        # (match_section), and unabbreviated "Section 1" sections
        # (match_section1)
        match_chapter = re.match('^(C|O)[A-Za-z]*(R|r)(\.|,|:|;)*$', raw.iloc[i]['text'])
        match_section = re.match('(S|s)[a-zA-Z]{2,3}(\.|,|:|;){0,2}$', raw.iloc[i]['text'])
        match_section1 = re.match('S[a-zA-Z]+$', raw.iloc[i]['text'])
        
        # Create a matching condition to check for three blank spaces above
        # potential matches
        blank3 = (re.match('^$', raw.iloc[i-1]['text']) and
                  re.match('^$', raw.iloc[i-2]['text']) and
                  re.match('^$', raw.iloc[i-3]['text']))
        
        # The following conditional statements check for situations that
        # indicate the beginning of a new chapter, a new section, or a new 
        # first section. If any of these are satisfied, the 'chapter' or 
        # 'section' variable is changed accordingly. Once all conditionals have
        # been checked, the resulting 'chapter' and 'section' values for the
        # word in question are added to their respective lists.
        # The results are two lists, one for each column, with a chapter and
        # section value for each row in the raw file.
        
        # Check for new chapters
        if (match_chapter and
            re.search('[0-9.]+(\.|,|:|;){0,2}', raw.iloc[i+1]['text']) and
            blank3):
            chapter = raw.iloc[i]['text'] +' '+ raw.iloc[i+1]['text']
        
        # Check for new abbreviated sections
        if ((match_section and re.search('^[0-9.\}]+(\.|,|:|;){0,2}$', raw.iloc[i+1]['text'])) or
            (match_section and blank3)):
            section = raw.iloc[i]['text'] +' '+ raw.iloc[i+1]['text']
            
        # Check for new unabbreviated "Section 1" sections
        if (match_section1 and
            re.search('^(1|.)(\.|,|:|;){0,2}$', raw.iloc[i+1]['text'])):
            section = raw.iloc[i]['text'] +' '+ raw.iloc[i+1]['text']
            
        # Set the "section" value to blank for areas of text belonging
        # to a chapter title and not an actual section
        if (match_chapter and
            re.search('[0-9.]+(\.|,|:|;){0,2}', raw.iloc[i+1]['text']) and
            blank3 !=  raw.iloc[i]['chapter']):
            section = ''
        
        # Add the resulting 'section' and 'chapter' values to their respective
        # lists.
        section_column.append(section)    
        chapter_column.append(chapter)

    # Once all words in the raw file have been checked, add the lists as
    # columns to the raw dataframe.
    raw['chapter'] = chapter_column
    raw['section'] = section_column

    # Add a chapter index to differentiate duplicate chapter headers
    raw["chapter_index"] = ((raw["chapter"].notna()) & (raw["chapter"]!=raw["chapter"].shift(1))).cumsum()
    
    # Add cell values for special cases
    raw.loc[((raw["chapter"]=="") & (raw["section"]=="")), ["chapter","section"]] = "Paratextual"
    raw.loc[((raw["chapter"]!="") & (raw["section"]=="")), ["section"]] = "Chapter_Title"
    raw.loc[((raw["chapter"]=="") & (raw["section"]!="")), ["chapter"]] = "Chapter_UNKNOWN"
    
    # Create the aggregate dataframe grouping words by their identified 
    # section assignments
    agg = raw[raw["text"]!=""].groupby(['chapter', 'section', 'chapter_index'], sort=False)['text'].apply(' '.join).reset_index()

    # Output the raw and aggregate dataframes as .csv files
    raw_outname = os.path.join("outputs","raw",filename.replace(".csv",'') + "_output.csv")
    agg_outname = os.path.join("outputs","agg",filename.replace(".csv",'') + "_aggregated_ouput.csv")

    raw.to_csv(raw_outname, index=False, encoding="utf-8-sig")
    agg.to_csv(agg_outname, index=False, encoding="utf-8-sig")


def main():
    
    # Set OCR output file directory path
    ocr_path = "."

    # Create directories for new raw/agg files
    parse_output_path = "."
    os.makedirs(os.path.join(parse_output_path,"outputs","agg"),exist_ok=True)
    os.makedirs(os.path.join(parse_output_path,"outputs","raw"),exist_ok=True)
    
    # Create a list of all raw OCR output files in corpus
    listdir = [f for f in os.listdir(ocr_path) if f.endswith(".tsv")]
    
    # Run "tsvparser" function in parallel to decrease compute time
    with joblib.parallel_backend(n_jobs=7,backend='loky'):
        joblib.Parallel(verbose=5)(joblib.delayed(tsvparser)(filename) for filename in listdir)
        

if __name__ == "__main__":
    main()