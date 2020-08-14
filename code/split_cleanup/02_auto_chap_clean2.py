# -*- coding: utf-8 -*-
"""
Created on Thu Aug  6 11:47:36 2020

@summary: This script corresponds to the "Step 4. Chapter Cleanup: Second 
    Automatic Pass" section of the Split Cleanup Jupyter notebook.
    The purpose of this script is twofold: 1) to integrate 
    manual changes made to the chapter list ("chapnumflags") files in the
    previous step and 2) to identify chapters missed by the initial splitting
    process. The script generates new raw and aggregate files to reflect all
    changes made as well as a report to indicate the automatic 'fixes' made by
    the script itself.
    

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
csv.field_size_limit(600000)


def skipfixes(raw_fix_pair):
    """    
    This function serves two purposes. First, it integrates changes made in the
    manual review process following the first round of automatic fixes to the raw
    file of each volume. It is important to note that the "chapnumfix" files were
    converted from .xlsx to .csv before this step. 
    
    Second, the function identifies chapters preceded by 
    numbering gaps and parses the text of the chapter immediately before them 
    for chapter headers that may have been missed by the original splitting process. 
    
    Previous to this step, the gaps were identified and marked by manual 
    reviewers. In short, the function receives as arguments both a raw file 
    and a "chapnumfixes" file for a given volume. After integrating the manual
    corrections made in this file, the function iterates through all chapters
    marked as being preceded by gaps. It then parses the text of chapters directly
    preceding each of these "gap" chapters and tries to identify chapter headers
    that may have been missed by the original splitting script. It does so by
    utilizing looser regular expressions and by searching for numbers that match
    those of the missing chapters. If missing chapters are identified, changes
    are made directly to the raw file of the volume in question.
    
    The function also collects metadata about chapters identified and corrections
    made. This metadata is compiled for each volume into a dictionary. Each of
    these volume-level dictionaries are then used to generate rows for a 
    corpus-level report intended to document the outcomes of the script.
    
    Arguments
    --------------------------------------------------------------------------    
    raw_fix_pair (list)         : Contains the string filepaths for both the 
                                  raw file and the "chapnumfixes" file for a 
                                  given volume.

    Returns
    --------------------------------------------------------------------------
    gap_fix_dict (dict)         : A dictionary containing the following
                                  information, to be included as a row 
                                  in a corpus-level report: the volume filename
                                  (str), and a list containing a description
                                  of the gap (str - "gap_title"), the chapter
                                  numbers of the missing chapters (list - 
                                  "possible_cor_nums"), and a list of potential
                                  correction candidates (list - "candidate_list"),
                                  the latter containing the candidate's chapter's
                                  title and starting index in the raw file.
    """
        
    #load files & create dataframes
    rawfile = raw_fix_pair[0]
    fixfile = raw_fix_pair[1]
    
    print(os.path.basename(rawfile))
    
    raw_df = pd.read_csv(rawfile, encoding='utf-8', low_memory=False)
    fix_df = pd.read_csv(fixfile, encoding='utf-8', low_memory=False)

    raw_df['chapter'] = raw_df['chapter'].replace(np.nan, '')
    raw_df['section'] = raw_df['section'].replace(np.nan, '')
    fix_df['gap'] = fix_df['gap'].replace(np.nan, '')
    raw_df['text'] = raw_df['text'].replace(np.nan, '')
    raw_df['chapter_index'] = raw_df['chapter_index'].replace(np.nan, '')
    raw_df["fix_chap_title"] = ""
    raw_df["raw_chap_num"] = ""
    raw_df["cor_chap_num"] = ""
    raw_df["chap_gap"] = ""
    raw_df["sug_chap_title"] = raw_df["chapter"]
    raw_df["sug_cor_chap_num"] = raw_df["cor_chap_num"]
    
    # match manual/automatic changes from first round of "chap_num_fixes"
    # match corrected chapter number and gap information from the chap_num_fixes file
    # to all rows in the raw file

    for i in range(0, fix_df.shape[0]):
        idx = fix_df.iloc[i]["chapter_index"]
        raw_df.loc[((raw_df["chapter_index"]==idx)), ["fix_chap_title"]] = fix_df.iloc[i]["chap_title"]
        raw_df.loc[((raw_df["chapter_index"]==idx)), ["raw_chap_num"]] = fix_df.iloc[i]["raw_num"]
        raw_df.loc[((raw_df["chapter_index"]==idx)), ["cor_chap_num"]] = fix_df.iloc[i]["corrected_num"]
        raw_df.loc[((raw_df["chapter_index"]==idx)), ["chap_gap"]] = fix_df.iloc[i]["gap"]

    raw_df['chap_gap'] = raw_df['chap_gap'].replace('', '0')
    raw_df['chap_gap'] = raw_df['chap_gap'].astype(int)
    raw_df["sug_cor_chap_num"] = raw_df["cor_chap_num"]
    raw_df["sug_cor_chap_num"] = raw_df['sug_cor_chap_num'].replace(np.nan, '')
    
    
    # Use gap metadata to identify and attempt to fix gaps
    raw_gaps = []

    gaps_df = raw_df.loc[(raw_df["chap_gap"] >=1 ), :]
    gaps_df = gaps_df[["cor_chap_num", "chap_gap"]]
    gaps_df = gaps_df.drop_duplicates()


    # for each gap found, compile a list of possible missing chapters
    # and search for them in the chapter preceding the gap.
    for idx1, row in gaps_df.iterrows():
        current_chap = row['cor_chap_num']
        previous_chap = raw_df.iloc[idx1-1]['cor_chap_num']
        candidate_list = []
        possible_cor_nums = [int(current_chap)-i for i in range(1,row['chap_gap']+1)]
        possible_cor_nums = list(reversed(possible_cor_nums))
        gap_title = "gap: " + str(previous_chap) + "-" + str(current_chap)
        prev_chap_rows = raw_df[raw_df['cor_chap_num'] == previous_chap].copy()
        prev_chap_rows['shift_text'] = prev_chap_rows.text.shift(-1)

        chap_matches = prev_chap_rows[(prev_chap_rows['text'].str.match(r'[^"]*HAPTER(\.|,|:|;)*$')==True) &
                                     (prev_chap_rows['shift_text'].str.match(r'[0-9.]+(\.|,|:|;){0,2}')==True)]

        
        # Add all potential correction candidates to a list
        for idx2, row in chap_matches.iterrows():
            if row['chapter'] != row['text'] +' '+ row['shift_text']:
                sug_chap_title = row['text'] +' '+ row['shift_text']
                missing_chap_start_index = idx2
                candidate_list.append({"sug_chap_title":sug_chap_title, 
                                        "missing_chap_start_index":missing_chap_start_index})


        # Conditionals for ID'ing missed chapters
        # and assigning suggested "corrected numbers".
        # This ensures that only candidate chapter headers that include
        # numbers known to belong to missing chapters are actually added
        # to the raw file. 
        # These conditionals account for different numbers of candidates found
        # and missing chapters contained in a gap
        if len(candidate_list) == 1 and len(possible_cor_nums) == 1:
            candidate_list[0]["sug_cor_chap_num"] = possible_cor_nums[0]
        elif len(candidate_list) > 1 and len(possible_cor_nums) == 1:
            for i in candidate_list:
                if str(possible_cor_nums[0]) in i["sug_chap_title"]:
                    i["sug_cor_chap_num"] = possible_cor_nums[0]
        elif len(candidate_list) == 1 and len(possible_cor_nums) > 1:
            for i in possible_cor_nums:
                if str(i) in candidate_list[0]["sug_chap_title"]:
                    candidate_list[0]["sug_cor_chap_num"] = i
        elif len(candidate_list) > 1 and len(possible_cor_nums) > 1:
            for i in candidate_list:
                for b in possible_cor_nums:
                    if str(b) in i["sug_chap_title"]:
                        i["sug_cor_chap_num"] = b

        
        # Integrate validated candidates into the raw file
        for c in candidate_list:
            if "sug_cor_chap_num" in c:
                raw_df.loc[c["missing_chap_start_index"]:idx1-1, "sug_chap_title"] = c["sug_chap_title"]
                raw_df.loc[c["missing_chap_start_index"]:idx1-1, "sug_cor_chap_num"] = c["sug_cor_chap_num"]
                newchap_df =  raw_df[c["missing_chap_start_index"]:idx1]
                for q in range(0, newchap_df.shape[0]):
                    if newchap_df.index.values[q] != c["missing_chap_start_index"]:
                        if newchap_df.iloc[q]['section'] != newchap_df.iloc[q-1]['section']:
                            raw_df.loc[c["missing_chap_start_index"]:newchap_df.index.values[q-1], "section"] = "Chapter_Title"
                            break
        
        # add gap information (list) for a given gap to a volume-level list
        raw_gaps.append([gap_title, possible_cor_nums, candidate_list])
    
    # Add the filename and volume-level list of gap information to a dictionary
    gap_fix_dict = {'file': rawfile, 'gaplist':raw_gaps}
    
    # create a new version of the raw file with adjusted chap numbers for output as .csv
    # Normalize chapter title language
    chapters_new = "CHAPTER " + raw_df["sug_cor_chap_num"].astype(str)
    raw_df['chapters_new'] = chapters_new
    raw_df.loc[(raw_df["sug_cor_chap_num"]==""), ["chapters_new"]] = raw_df["chapter"]
    adjusted_raw = pd.concat([raw_df["left"].copy(),
                              raw_df["top"].copy(),
                              raw_df["width"].copy(),
                              raw_df["height"].copy(),
                              raw_df["conf"].copy(),
                              raw_df["text"].copy(),
                              raw_df["name"].copy(),
                              raw_df["chapters_new"].copy(),
                              raw_df["section"].copy()], axis=1)

    adjusted_raw.columns = ["left", "top", "width", "height", "conf", "text", "name", "chapter", "section"]
    adjusted_raw.loc[(adjusted_raw["chapter"]=="CHAPTER "), ["chapter"]] = ""

    adjusted_raw["chapter_index"] = ((adjusted_raw["chapter"].notna()) & (adjusted_raw["chapter"]!=adjusted_raw["chapter"].shift(1))).cumsum()

    adjusted_raw.loc[((adjusted_raw["chapter"]=="") & (adjusted_raw["section"]=="")), ["chapter","section"]] = "Paratextual"
    adjusted_raw.loc[((adjusted_raw["chapter"]!="") & (adjusted_raw["section"]=="")), ["section"]] = "Chapter_Title"
    adjusted_raw.loc[((adjusted_raw["chapter"]=="") & (adjusted_raw["section"]!="")), ["chapter"]] = "Chapter_UNKNOWN"
    
    # Create a new aggregate dataframe for output as a .csv
    agg = adjusted_raw[adjusted_raw["text"]!=""].groupby(['chapter', 'section', 'chapter_index'], sort=False)['text'].apply(' '.join).reset_index()
    
    #output new raw and agg files to .csv
    raw_outname = rawfile.replace("_output.csv", "_output_chapadjusted.csv")
    raw_outname = raw_outname.replace("./agg_raw_indices/outputs/raw/", "./skip_fixes/raw/")
    agg_outname = rawfile.replace("_output.csv", "_aggregated_chapadjusted.csv")
    agg_outname = agg_outname.replace("./agg_raw_indices/outputs/raw/", "./skip_fixes/agg/")
    
    
    adjusted_raw.to_csv(raw_outname, index=False, encoding="utf-8-sig")
    agg.to_csv(agg_outname, index=False, encoding="utf-8-sig")
    
    #return dictionary so that all can be written to file for future reference about which fixes were made, which weren't, etc.
    return gap_fix_dict




def generate_report(gap_fix_dict_list):
    """    
    This function generates a corpus-level report file for the corrections made
    by the 'skipfixes' function. Each row contains an estimated total number 
    of missing chapters (total_missing_not_comprehensive), a list of 
    corrections made (fixes_made), a count of fixes made (total_fixes), and a 
    list of missing chapters that were not identified and corrected by the 
    script (still_missing_chaps_not_comprehensive). 
    
    Arguments
    --------------------------------------------------------------------------    
    gap_fix_dict_list (list)    : Contains a list of dictionaries, one for each
                                  volume. See above for the information contained
                                  in each. The dictionaries contain information
                                  for each volume that will be used to compile
                                  an individual row for the report. 

    Returns
    --------------------------------------------------------------------------
    N/A
    """    
    
    
    meta_fixes = []
    
    
    for i in gap_fix_dict_list:
        meta_d = {}
        #get the file name in which the fixes have been made. Shorten as much as possible
        file = os.path.basename(i['file'])
        file = file.replace("_output.csv", "")
        meta_d['file']=file

        # get the total number of gaps found in that volume (CAN BE ZERO)
        meta_d['total_gaps_identified_not_comprehensive'] = len(i['gaplist'])
        total_missing = 0
        all_missing = []
        still_missing= []
        fixes_made = []

        # get a list of all the missing chapters. If the gap list is greater 
        # than one, iterate through gap list. Append all items of the 
        # list at index 1 of each list to the total missing chapters list

        if len(i['gaplist']) > 0:
            for b in range(0, len(i['gaplist'])):
                for k in i['gaplist'][b][1]:
                    all_missing.append(k)
                    still_missing.append(k) 
                    
        # if any gaps exist for that volume, find the fixes by finding those 
        # gap-lists with lists of fix dictionaries that have lengths longer than 1

        if len(i['gaplist']) > 0:
            for b in range(0, len(i['gaplist'])):
                if len(i['gaplist'][b][2]) > 0:
                    for j in i['gaplist'][b][2]:
                        if 'sug_cor_chap_num' in j:
                            fixes_made.append(j['sug_cor_chap_num'])
                            if j['sug_cor_chap_num'] in still_missing:
                                still_missing.remove(j['sug_cor_chap_num'])

        # Compile a row 
        fixes_total = len(fixes_made)
        total_missing = len(all_missing)
        meta_d['total_missing_not_comprehensive'] = total_missing
        meta_d['total_fixes'] = fixes_total
        meta_d['fixes_made'] = fixes_made
        meta_d['still_missing_chaps_not_comprehensive'] = still_missing
        meta_fixes.append(meta_d)

    # Output the compiled report to .csv
    meta_df = pd.DataFrame(meta_fixes)
    meta_df.to_csv("skip_fixes_report.csv", index=False, encoding="utf-8-sig")








def main():
    # Set directories for raw and "chapnumfixe" files
    raw_path = r"C:\Users\npbyers\Desktop\OTB\ChapNumFixes\agg_raw_indices\outputs\raw"
    fix_path = r"C:\Users\npbyers\Desktop\OTB\ChapNumFixes\new_chap_fixes_csv_indexed"
    
    rawfolder = "./agg_raw_indices/outputs/raw/"
    fixfolder = "./new_chap_fixes_csv_indexed/"
    
    # Create filepath lists for both sets of files
    raw_filelist = [(rawfolder + f) for f in os.listdir(raw_path) if f.endswith(".csv")]
    fix_filelist = [(fixfolder + f) for f in os.listdir(fix_path) if f.endswith(".csv")]
    
    # Create a list of pairs, each containing the path for a raw file
    # and "chapnumfixes" file for a given volume
    raw_fix_pairs = []
    for i in range(0, len(raw_filelist)):
        raw_fix_pairs.append([raw_filelist[i], fix_filelist[i]])
    
    # Run the 'skipfixes' function in parallel to reduce compute time
    with joblib.parallel_backend(n_jobs=7,backend='loky'):
        gap_fix_dict_list = joblib.Parallel(verbose=5)(
        joblib.delayed(skipfixes)(pair) for pair in raw_fix_pairs)
    
    # Generate the corpus-level report for this step
    generate_report(gap_fix_dict_list)
    

if __name__ == "__main__":
    main()

