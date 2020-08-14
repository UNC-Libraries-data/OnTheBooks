# -*- coding: utf-8 -*-
"""
Created on Thu Aug  6 10:28:19 2020

@summary: This script corresponds to the "Step 2. Chapter Cleanup: 
    First Automatic Pass" section of the Split Cleanup Jupyter notebook  
    documentation. This script generates a group of excel files, one for each 
    volume, with chapter errors identified and with certain suggested 
    corrections ("chapnumflags" files). These files are then utilized in the 
    "Step 3. Chapter Cleanup: First Manual Pass" section of the Split
    Cleanup Jupyter notebook.

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
import xlsxwriter
csv.field_size_limit(600000)

# Create a variable to store all automatic fix/recommendation data for each volume
# This will later be used to output a report file for this step     
meta_list=[]


def initial_chap_fixes(agg_folder, agg_file):
    """    
    This function identifies chapter split numbering errors, suggests corrections
    for certain situtations, and outputs a volume-level list of chapters with
    potential errors and suggested corrections flagged for manual review.
    The function does not provide any return values. Instead, it outputs a
    single Excel file for each volume and adds volume-level metadata to the 
    corpus-level report list ("meta_list")
    
    Arguments
    --------------------------------------------------------------------------    
    agg_folder (str)         : The string filepath for the directory containing
                               the corpus "aggregate" files
    agg_file (str)           : The string base file name for an individual
                               volume's "aggregate" file
                         
    Returns
    --------------------------------------------------------------------------
    N/A
    
    """
    
    # Create path string variables and import the agg file into a Pandas dataframe
    inpath = agg_folder + agg_file
      
    outpath = inpath.replace("chap_adjusted_agg", "chap_num_flags")
    outpath = outpath.replace("aggregated_chapadjusted.csv", "chapnumflags.xlsx")
    
    vol_df = pd.read_csv(inpath, encoding = 'utf-8-sig')

    # Create lists to be converted to series for a chapter-level dataframe that
    # will be exported as an excel file
    chap_headers = []
    chap_indices = []
    chap_nums_raw = []


    # Populate the above lists
    if vol_df.loc[0,"chapter"]=="Paratextual":
        for idx, row in vol_df.iterrows():
                if idx > 0:
                    if vol_df.loc[idx,"chapter"] != vol_df.loc[idx-1,"chapter"]:
                        chap_headers.append(vol_df.loc[idx,"chapter"])
                        chap_indices.append(vol_df.loc[idx,"chapter_index"])
    else:
        for idx, row in vol_df.iterrows():
            if idx==0:
                chap_headers.append(vol_df.loc[idx,"chapter"])
                chap_indices.append(vol_df.loc[idx,"chapter_index"])
            elif vol_df.loc[idx,"chapter"] != vol_df.loc[idx-1,"chapter"]:
                    chap_headers.append(vol_df.loc[idx,"chapter"])
                    chap_indices.append(vol_df.loc[idx,"chapter_index"])
    for i in range(0,len(chap_headers)):

        try:
            chapter_num = chap_headers[i].split()[1]
            chapter_num = chapter_num.rstrip(punctuation)
            chap_nums_raw.append(chapter_num)
        except:
            chap_nums_raw.append("N/A")

    # Convert the above lists to series
    # Create a stable list of the original numbering for
    # Comparison purposes
    raw_titles = pd.Series(chap_headers)
    indices_Series = pd.Series(chap_indices)
    unq_ch = pd.Series(pd.to_numeric(chap_nums_raw, errors="coerce"))
    orig_num = unq_ch.copy()



    # Complete all lag3, lag2, and lag1 fixes
    for row_num in range(3,len(unq_ch)-3):
        if unq_ch[row_num]!= (unq_ch[row_num+1]-1) and unq_ch[row_num]!= (unq_ch[row_num-1]+1):
            lag1_test = (unq_ch[row_num+1]-unq_ch[row_num-1])==2
            lag2_test = (unq_ch[row_num+2]-unq_ch[row_num-2])==4 and unq_ch[row_num+2]-unq_ch[row_num+1]==1
            lag3_test = (unq_ch[row_num+3]-unq_ch[row_num-3])==6 and unq_ch[row_num+3]-unq_ch[row_num+2]==1

            if lag1_test and lag2_test and lag3_test:
                unq_ch[row_num] = unq_ch[row_num-3]+3 

    for row_num in range(2,len(unq_ch)-2):
        if unq_ch[row_num]!= (unq_ch[row_num+1]-1) and unq_ch[row_num]!= (unq_ch[row_num-1]+1):
            lag1_test = (unq_ch[row_num+1]-unq_ch[row_num-1])==2
            lag2_test = (unq_ch[row_num+2]-unq_ch[row_num-2])==4 and unq_ch[row_num+2]-unq_ch[row_num+1]==1
            if lag1_test and lag2_test:
                unq_ch[row_num] = unq_ch[row_num-2]+2

    for row_num in range(1,len(unq_ch)-1):
        if unq_ch[row_num]!= (unq_ch[row_num+1]-1) and unq_ch[row_num]!= (unq_ch[row_num-1]+1):
            lag1_test = (unq_ch[row_num+1]-unq_ch[row_num-1])==2
            if lag1_test:
                unq_ch[row_num] = unq_ch[row_num-1]+1

    # Parse chapter rows in groups of 5 to flag areas with potential errors
    # Mark those chapters that were corrected by the lag fix steps above
    max_diff = unq_ch.diff(1).rolling(window=5, center=True).max()
    min_diff = unq_ch.diff(1).rolling(window=5, center=True).min()
    flag = ~((max_diff == min_diff) & max_diff == 1)
    corrected = np.logical_and(unq_ch != orig_num, np.isnan(unq_ch)==False)

    # Compile dataframe to be exported as an excel file
    output = pd.concat([raw_titles, orig_num, indices_Series, unq_ch, corrected, flag], axis=1)
    output.columns = ['chap_title', 'raw_num', 'chapter_index', 'corrected_num', 'correction_made', 'flag']

    # Create an excel workbook from the above dataframe, add formatting to make
    # corrections an errors more easily findable, and save.
    with pd.ExcelWriter(outpath, engine='xlsxwriter') as writer:

        # create workbook object
        workbook = writer.book

        header_format = workbook.add_format({'bold': True,
                                             'valign': 'vcenter',
                                             'border': 1,
                                             'bg_color': '#e2efda',
                                             'font_size': 14})
        flag_format = workbook.add_format({'bg_color': '#f8cbad'})
        corrected_format = workbook.add_format({'bg_color': '#b7dee8'})


        # Convert the dataframe to an XlsxWriter Excel object.
        output.to_excel(writer, sheet_name='op', index=False, startrow=1, header=False)
        outputSheet = writer.sheets['op']
        for col_num, value in enumerate(output.columns.values):
            outputSheet.write(0, col_num, value, header_format)
        outputSheet.set_column(0, 0, 13)
        outputSheet.set_column(1, 1, 10)
        outputSheet.set_column(2, 2, 16)
        outputSheet.set_column(3, 3, 18)
        outputSheet.set_column(4, 4, 9)

        outputSheet.conditional_format('F2:F'+str(output.shape[0]+1), {'type':     'cell',
                                            'criteria': 'equal to',
                                            'value':    "True",
                                            'format':   flag_format})
        outputSheet.conditional_format('E2:E'+str(output.shape[0]+1), {'type':     'cell',
                                            'criteria': 'equal to',
                                            'value':    "True",
                                            'format':   corrected_format})

        writer.save()
        
    
    # Add fix metadata for the volume in question to the corpus-level list
    # This list will be saved as a report .csv file
    try:
        corrections = corrected.value_counts()[1]
    except:
        corrections = 0
    meta_list.append({"agg_file":agg_file, 
          "chap_count":output.shape[0], 
          "flags":flag.value_counts()[1], 
          "corrections":corrections})



def main():
    # Set the filepath variable for the directory containing the corpus
    # aggregate files
    agg_filelist = os.listdir(r"C:\Users\npbyers\Desktop\OTB\ChapNumFixes\chap_adjusted_agg")
    agg_folder = "./chap_adjusted_agg/"
    
    # Perform chapter fix/report operations for each volume using the 
    # "initial_chap_fixes" function
    for agg_file in agg_filelist:
        initial_chap_fixes(agg_folder, agg_file)
        
    # Compile the corpus-level report for this step and output it to a .csv file
    meta = pd.DataFrame(meta_list)
    meta.to_csv("chap_nums_check.csv")

if __name__ == "__main__":
    main()