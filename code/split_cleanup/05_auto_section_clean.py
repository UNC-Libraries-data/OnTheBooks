# -*- coding: utf-8 -*-
"""
Created on Thu Aug  6 09:41:31 2020

@summary: This script corresponds to the "Step 6. Section Cleanup: Automatic 
    Corrections" section of the Split Cleanup Jupyter notebook 
    documentation. The purpose of this script is to automatically identify 
    and correct as many section split errors as possible. The operations
    herein are performed using on raw files themselves. The script generates 
    1) a new round of raw files, 2) a report on fixes made to each volume, 
    and 3) a "weird_chaps" file consisting of rows with all sections for all 
    chapters containing sections with suspicious gap values. The latter file 
    will be used by manual reviewers in "Step 7. Section Cleanup: Manual 
    Corrections" to aid in correcting the most obvious and easily-corrected 
    errors.

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

def get_nums_from_str(shift_text):
    """    
    Used in Operation 10 to extract section numbers from garbled or messy 
    text fields in the raw file. 
    
    Arguments
    --------------------------------------------------------------------------    
    shift_text (str)         : The raw "text" value from the row following a 
                               potential section header
                         
    Returns
    --------------------------------------------------------------------------
    unbroken_num (int)       : The extracted section number
    
    """
    
    unbroken_num = ""
    for l in range(0,len(shift_text)):
        if shift_text[l].isdigit():
            unbroken_num = unbroken_num + shift_text[l]
        else:
            break
    if unbroken_num != "":
        unbroken_num = int(unbroken_num)

    return unbroken_num


def run_fixes(raw_file):
    """    
    Parses the section information in each volume. Attempts to identify and 
    correct potential section split errors. The function consists of 10 
    separate operations run in sequence, each of which attempts to solve a 
    different type of potential section split error. Once all operations have 
    run, new 'raw' and aggregate files are compiled and exported to .csv.
    Along with these two new files (one set for each volume), information for 
    two separate corpus-level report files is compiled during the processing 
    of each volume. One consists of fix metadata detailing the number of 
    corrections made by each operation, the number of remaining errors, etc. 
    The second file consists of all section rows from the entire corpus for 
    all chapters containing sections with suspicious gaps. This second file 
    is used to identify areas where potentially easy manual corrections could 
    be made following the automatic cleanup process.
    
    Arguments
    --------------------------------------------------------------------------    
    raw_file (str)           : The "raw" file path for a single volume
                         
    Returns
    --------------------------------------------------------------------------
    report_row (dict)        : The fix report metadata for the entire volume. 
                               Also contains a list of dictionaries containing 
                               section information for chapters containing at 
                               least one section with a suspicious gap.
    
    """
    
    fixes = 0

    raw_df = pd.read_csv(raw_file, encoding='utf-8', low_memory=False)

    raw_df['chapter'] = raw_df['chapter'].replace(np.nan, '')
    raw_df['section'] = raw_df['section'].replace(np.nan, '')
    if 'transcription_here' in raw_df.columns:
        raw_df.drop(columns=['transcription_here'])
    raw_df['text'] = raw_df['text'].replace(np.nan, '')

    #reset chapter_index
    raw_df["chapter_index"] = (raw_df.chapter != raw_df.chapter.shift(1)).cumsum()
    raw_df['chapter_index'] = raw_df['chapter_index'].replace(np.nan, '')

    #set section index
    raw_df["section_index"] = (raw_df.section != raw_df.section.shift(1)).groupby(raw_df.chapter).cumsum()

    sections = raw_df.loc[:, ['chapter', 'chapter_index', 'section', 'section_index']].drop_duplicates()
    sections['raw_num'] = sections['section'].apply(lambda x: 0 if x == "Chapter_Title" else (x.strip().split()[1].rstrip(punctuation) if " " in x.strip() and x.strip().split()[1].rstrip(punctuation).isnumeric() else np.nan))
    chapters = sections.groupby('chapter_index')

    # Operation 1
    # non-numeric section header fixes
    non_numeric = 0
    for b in chapters.groups.keys():
        chap_sects = chapters.get_group(b)

        for i in range(0,chap_sects.shape[0]):
            has_digits = str(chap_sects.iloc[i]['raw_num']).isnumeric()
            paratextual = chap_sects.iloc[i]['section'] == "Paratextual"

            if not has_digits and not paratextual:

                if i!=0:
                    lag = 1
                    for k in range(1,i+1):
                        if str(chap_sects.iloc[i-k]['raw_num']).isnumeric():
                            break
                        lag+=1

                    raw_df.loc[((raw_df["section_index"]==chap_sects.iloc[i]['section_index']) & (raw_df["chapter_index"]==chap_sects.iloc[i]['chapter_index'])), ["section"]] = chap_sects.iloc[i-lag]['section']
                    fixes+=1
                    non_numeric+=1

                else:
                    continue

    raw_df["section_index"] = (raw_df.section != raw_df.section.shift(1)).groupby(raw_df.chapter).cumsum()
    sections = raw_df.loc[:, ['chapter', 'chapter_index', 'section', 'section_index']].drop_duplicates()
    sections['raw_num'] = sections['section'].apply(lambda x: 0 if x == "Chapter_Title" else (x.strip().split()[1].rstrip(punctuation) if " " in x.strip() and x.strip().split()[1].rstrip(punctuation).isnumeric() else np.nan))
    sections.loc[sections["section"]=="Paratextual", "raw_num"] = 0
    chapters = sections.groupby('chapter_index')

    
    # Operation 2
    # Deals with all of the external section references as well as subsections in the session_laws volumes
    external_refs = 0

    # 2.1 - Remove all non-Section-1 "Section" splits from between Chapter_Title and actual Section 1
    for b in chapters.groups.keys():
        chap_sects = chapters.get_group(b)


        for i in range(0,chap_sects.shape[0]):

            section_full = chap_sects.iloc[i]['section'].lower().find("section") != -1
            not_one = chap_sects.iloc[i]['raw_num'] != '1'

            if i!=0:
                if section_full and not_one:
                    raw_df.loc[((raw_df["section_index"]==chap_sects.iloc[i]['section_index']) & (raw_df["chapter_index"]==chap_sects.iloc[i]['chapter_index'])), ["section"]] = chap_sects.iloc[0]['section']
                    fixes += 1
                else:
                    break

    raw_df["section_index"] = (raw_df.section != raw_df.section.shift(1)).groupby(raw_df.chapter).cumsum()
    sections = raw_df.loc[:, ['chapter', 'chapter_index', 'section', 'section_index']].drop_duplicates()
    sections['raw_num'] = sections['section'].apply(lambda x: 0 if x == "Chapter_Title" else (x.strip().split()[1].rstrip(punctuation) if " " in x.strip() and x.strip().split()[1].rstrip(punctuation).isnumeric() else np.nan))
    sections.loc[sections["section"]=="Paratextual", "raw_num"] = 0
    chapters = sections.groupby('chapter_index')

    # 2.2 - Remove all "Section" splits following the first "Section 1"
    for b in chapters.groups.keys():
        chap_sects = chapters.get_group(b)

        for i in range(0,chap_sects.shape[0]):

            external_ref = chap_sects.iloc[i]['section'].lower().find("section") != -1 and chap_sects.iloc[i]['section_index'] != 2   

            if external_ref:
                if i!=0:
                    lag = 1
                    for k in range(1,i+1):
                        if "section" in chap_sects.iloc[i-k]['section'].lower() and chap_sects.iloc[i-k]['section_index'] == 2:
                            break
                        elif "section" not in chap_sects.iloc[i-k]['section'].lower():
                            break
                        lag+=1

                    raw_df.loc[((raw_df["section_index"]==chap_sects.iloc[i]['section_index']) & (raw_df["chapter_index"]==chap_sects.iloc[i]['chapter_index'])), ["section"]] = chap_sects.iloc[i-lag]['section']
                    fixes += 1
                    external_refs+=1



    raw_df["section_index"] = (raw_df.section != raw_df.section.shift(1)).groupby(raw_df.chapter).cumsum()
    sections = raw_df.loc[:, ['chapter', 'chapter_index', 'section', 'section_index']].drop_duplicates()
    sections['raw_num'] = sections['section'].apply(lambda x: 0 if x == "Chapter_Title" else (x.strip().split()[1].rstrip(punctuation) if " " in x.strip() and x.strip().split()[1].rstrip(punctuation).isnumeric() else np.nan))
    sections.loc[sections["section"]=="Paratextual", "raw_num"] = 0
    chapters = sections.groupby('chapter_index')
        
    # Operation 3
    # Fixes situations in which "south" or "September" were mistaken for sections 
    south_sept_fixes = 0
    for b in chapters.groups.keys():
        chap_sects = chapters.get_group(b)


        for i in range(0,chap_sects.shape[0]):

            south_sept = chap_sects.iloc[i]['section'].lower().find("south") != -1 or chap_sects.iloc[i]['section'].lower().find("september") != -1

            if south_sept:
                if i!=0:
                    lag = 1
                    for k in range(1,i+1):
                        if "south" not in chap_sects.iloc[i-k]['section'].lower() and "september" not in chap_sects.iloc[i-k]['section'].lower():
                            break
                        lag+=1

                    raw_df.loc[((raw_df["section_index"]==chap_sects.iloc[i]['section_index']) & (raw_df["chapter_index"]==chap_sects.iloc[i]['chapter_index'])), ["section"]] = chap_sects.iloc[i-lag]['section']
                    fixes += 1
                    south_sept_fixes+=1
                else:
                    continue
    raw_df["section_index"] = (raw_df.section != raw_df.section.shift(1)).groupby(raw_df.chapter).cumsum()
    sections = raw_df.loc[:, ['chapter', 'chapter_index', 'section', 'section_index']].drop_duplicates()
    sections['raw_num'] = sections['section'].apply(lambda x: 0 if x == "Chapter_Title" else (x.strip().split()[1].rstrip(punctuation) if " " in x.strip() and x.strip().split()[1].rstrip(punctuation).isnumeric() else np.nan))
    sections.loc[sections["section"]=="Paratextual", "raw_num"] = 0
    chapters = sections.groupby('chapter_index')

    
    # Operation 4
    # Lag 3 fixes
    lag3 = 0    
    for b in chapters.groups.keys():
        chap_sects = chapters.get_group(b)
        if chap_sects.shape[0] > 7:
            for row_num in range(3,chap_sects.shape[0]-3):

                current_raw_num = int(chap_sects.iloc[row_num]['raw_num'])
                minus_one = int(chap_sects.iloc[row_num-1]['raw_num'])
                minus_two = int(chap_sects.iloc[row_num-2]['raw_num'])
                minus_three = int(chap_sects.iloc[row_num-3]['raw_num'])
                plus_one = int(chap_sects.iloc[row_num+1]['raw_num'])
                plus_two = int(chap_sects.iloc[row_num+2]['raw_num'])
                plus_three = int(chap_sects.iloc[row_num+3]['raw_num'])           

                if current_raw_num != (plus_one-1) and current_raw_num != (minus_one+1):
                    lag1_test = (plus_one-minus_one)==2
                    lag2_test = (plus_two-minus_two)==4 and plus_two-plus_one==1
                    lag3_test = (plus_three-minus_three)==6 and plus_three-plus_two==1

                    if lag1_test and lag2_test and lag3_test:

                        raw_df.loc[((raw_df["section_index"]==chap_sects.iloc[row_num]['section_index']) & (raw_df["chapter_index"]==chap_sects.iloc[row_num]['chapter_index'])), ["section"]] =  "Sec. " + str(minus_three+3) + "."
                        fixes+=1
                        lag3 += 1


    raw_df["section_index"] = (raw_df.section != raw_df.section.shift(1)).groupby(raw_df.chapter).cumsum()
    sections = raw_df.loc[:, ['chapter', 'chapter_index', 'section', 'section_index']].drop_duplicates()
    sections['raw_num'] = sections['section'].apply(lambda x: 0 if x == "Chapter_Title" else (x.strip().split()[1].rstrip(punctuation) if " " in x.strip() and x.strip().split()[1].rstrip(punctuation).isnumeric() else np.nan))
    sections.loc[sections["section"]=="Paratextual", "raw_num"] = 0
    chapters = sections.groupby('chapter_index')


    # Operation 5
    # Lag 2 fixes
    lag2 = 0
    for b in chapters.groups.keys():
        chap_sects = chapters.get_group(b)
        if chap_sects.shape[0] > 5:
            for row_num in range(2,chap_sects.shape[0]-2):

                current_raw_num = int(chap_sects.iloc[row_num]['raw_num'])
                minus_one = int(chap_sects.iloc[row_num-1]['raw_num'])
                minus_two = int(chap_sects.iloc[row_num-2]['raw_num'])
                plus_one = int(chap_sects.iloc[row_num+1]['raw_num'])
                plus_two = int(chap_sects.iloc[row_num+2]['raw_num'])        

                if current_raw_num != (plus_one-1) and current_raw_num != (minus_one+1):
                    lag1_test = (plus_one-minus_one)==2
                    lag2_test = (plus_two-minus_two)==4 and plus_two-plus_one==1

                    if lag1_test and lag2_test:

                        raw_df.loc[((raw_df["section_index"]==chap_sects.iloc[row_num]['section_index']) & (raw_df["chapter_index"]==chap_sects.iloc[row_num]['chapter_index'])), ["section"]] =  "Sec. " + str(minus_two+2) + "."
                        fixes+=1
                        lag2+=1


    raw_df["section_index"] = (raw_df.section != raw_df.section.shift(1)).groupby(raw_df.chapter).cumsum()
    sections = raw_df.loc[:, ['chapter', 'chapter_index', 'section', 'section_index']].drop_duplicates()
    sections['raw_num'] = sections['section'].apply(lambda x: 0 if x == "Chapter_Title" else (x.strip().split()[1].rstrip(punctuation) if " " in x.strip() and x.strip().split()[1].rstrip(punctuation).isnumeric() else np.nan))
    sections.loc[sections["section"]=="Paratextual", "raw_num"] = 0
    chapters = sections.groupby('chapter_index')


    # Operation 6
    # Lag 1 fixes
    lag1 = 0
    for b in chapters.groups.keys():
        chap_sects = chapters.get_group(b)
        if chap_sects.shape[0] > 3:
            for row_num in range(1,chap_sects.shape[0]-1):

                current_raw_num = int(chap_sects.iloc[row_num]['raw_num'])
                minus_one = int(chap_sects.iloc[row_num-1]['raw_num'])
                plus_one = int(chap_sects.iloc[row_num+1]['raw_num'])
                
                if current_raw_num != (plus_one-1) and current_raw_num != (minus_one+1):
                    lag1_test = (plus_one-minus_one)==2

                    if lag1_test:
                        raw_df.loc[((raw_df["section_index"]==chap_sects.iloc[row_num]['section_index']) & (raw_df["chapter_index"]==chap_sects.iloc[row_num]['chapter_index'])), ["section"]] =  "Sec. " + str(minus_one+1) + "."
                        fixes+=1
                        lag1+=1

    raw_df["section_index"] = (raw_df.section != raw_df.section.shift(1)).groupby(raw_df.chapter).cumsum()
    sections = raw_df.loc[:, ['chapter', 'chapter_index', 'section', 'section_index']].drop_duplicates()
    sections['raw_num'] = sections['section'].apply(lambda x: 0 if x == "Chapter_Title" else (x.strip().split()[1].rstrip(punctuation) if " " in x.strip() and x.strip().split()[1].rstrip(punctuation).isnumeric() else np.nan))
    sections.loc[sections["section"]=="Paratextual", "raw_num"] = 0
    chapters = sections.groupby('chapter_index')


    # generate "gap" data to find missing chapters for Operations 7-10
    sections['raw_num'] = sections['raw_num'].astype(float)
    sections["gap"] = chapters.raw_num.diff(1)

    # Operation 7
    # Fix suspicious number inserts based on gap info
    # For example: 1-2-3-394-4-5-6
    weird_inserts = 0
    run_fixes = 1
    while run_fixes != 0:
        run_fixes = 0
        for r in range(0, sections.shape[0]):
            gap_before = sections.iloc[r-1]['gap']
            gap = sections.iloc[r]['gap']
            try:
                gap_after = sections.iloc[r+1]['gap']
            except:
                gap_after = 1
            if gap != 1 and gap != 0 and gap_before == 1 and gap_after == (gap+(-2*gap)+1):
                raw_df.loc[((raw_df["section_index"]==sections.iloc[r]['section_index']) & (raw_df["chapter_index"]==sections.iloc[r]['chapter_index'])), ["section"]] =  sections.iloc[r-1]['section']
                fixes+=1
                run_fixes+=1
                weird_inserts+=1

        raw_df["section_index"] = (raw_df.section != raw_df.section.shift(1)).groupby(raw_df.chapter).cumsum()
        sections = raw_df.loc[:, ['chapter', 'chapter_index', 'section', 'section_index']].drop_duplicates()
        sections['raw_num'] = sections['section'].apply(lambda x: 0 if x == "Chapter_Title" else (x.strip().split()[1].rstrip(punctuation) if " " in x.strip() and x.strip().split()[1].rstrip(punctuation).isnumeric() else np.nan))
        sections.loc[sections["section"]=="Paratextual", "raw_num"] = 0
        sections['raw_num'] = sections['raw_num'].astype(float)
        chapters = sections.groupby('chapter_index')
        sections["gap"] = chapters.raw_num.diff(1)




    # Operation 8
    # This fixes situations in which section 3 is mistaken for section 8, 
    # where Chapter_Title through Sec. 2 are consecutive beforehand
    one_two_eight = 0
    for r in range(0, sections.shape[0]):
        num_before = sections.iloc[r-1]['raw_num']
        num = sections.iloc[r]['raw_num']
        gap = sections.iloc[r]['gap']


        sec_three_as_eight = ((gap == 6 and num == 8) or (gap == 36 and num == 38)) and num_before == 2

        if sec_three_as_eight:
            raw_df.loc[((raw_df["section_index"]==sections.iloc[r]['section_index']) & (raw_df["chapter_index"]==sections.iloc[r]['chapter_index'])), ["section"]] =  "Sec. 3."
            fixes+=1
            one_two_eight+=1

    raw_df["section_index"] = (raw_df.section != raw_df.section.shift(1)).groupby(raw_df.chapter).cumsum()
    sections = raw_df.loc[:, ['chapter', 'chapter_index', 'section', 'section_index']].drop_duplicates()
    sections['raw_num'] = sections['section'].apply(lambda x: 0 if x == "Chapter_Title" else (x.strip().split()[1].rstrip(punctuation) if " " in x.strip() and x.strip().split()[1].rstrip(punctuation).isnumeric() else np.nan))
    sections.loc[sections["section"]=="Paratextual", "raw_num"] = 0
    sections['raw_num'] = sections['raw_num'].astype(float)
    chapters = sections.groupby('chapter_index')
    sections["gap"] = chapters.raw_num.diff(1)        




    # Operation 9
    #This fixes situations in which a 3 in any digit position has been mistaken 
    # for an 8, but a gap nearby has prevented the lag fix from catching it
    three_eight_gaps = 0
    for r in range(3, sections.shape[0]-3):
        current_gap = sections.iloc[r]['gap']
        current_raw_num = sections.iloc[r]['raw_num']
        string_raw_num = str(int(current_raw_num))

        minus_one = sections.iloc[r-1]['raw_num']
        minus_two = sections.iloc[r-2]['raw_num']
        minus_three = sections.iloc[r-3]['raw_num']
        plus_one = sections.iloc[r+1]['raw_num']
        plus_two = sections.iloc[r+2]['raw_num']
        plus_three = sections.iloc[r+3]['raw_num']



        if current_gap > 3:     
            for l in range(0,len(string_raw_num)):
                if string_raw_num[l] == "8":
                    new_string = string_raw_num[:l] + "3" + string_raw_num[l+1:]
                    new_num = float(new_string)

                    if (new_num-minus_one<=2 and new_num+1==plus_one) or (plus_one-new_num<=2 and new_num-1==minus_one):



                        raw_df.loc[((raw_df["section_index"]==sections.iloc[r]['section_index']) & (raw_df["chapter_index"]==sections.iloc[r]['chapter_index'])), ["section"]] =  "Sec. " + new_string
                        fixes+=1
                        three_eight_gaps+=1

                        break

    raw_df["section_index"] = (raw_df.section != raw_df.section.shift(1)).groupby(raw_df.chapter).cumsum()
    sections = raw_df.loc[:, ['chapter', 'chapter_index', 'section', 'section_index']].drop_duplicates()
    sections['raw_num'] = sections['section'].apply(lambda x: 0 if x == "Chapter_Title" else (x.strip().split()[1].rstrip(punctuation) if " " in x.strip() and x.strip().split()[1].rstrip(punctuation).isnumeric() else np.nan))
    sections.loc[sections["section"]=="Paratextual", "raw_num"] = 0
    sections['raw_num'] = sections['raw_num'].astype(float)
    chapters = sections.groupby('chapter_index')
    sections["gap"] = chapters.raw_num.diff(1)


    # Operation 10
    # Examines gaps of 2-4 and tries to find section headers
    # that were missed by the original splits.
    skip_fixes = 0

    gaps_df = sections.loc[((sections["gap"] >= 2) & (sections["gap"] <5)), :]

    for idx1, row in gaps_df.iterrows():
        current_gap = row['gap']
        current_sec_num = row['raw_num']
        current_sec_index = row['section_index']
        current_chapter_index = row['chapter_index']

        previous_sec = sections.loc[((sections["section_index"]==current_sec_index-1) & (sections["chapter_index"]==current_chapter_index)), :].reset_index()['section'][0]
        previous_sec_index = current_sec_index-1

        candidate_list = []
        possible_cor_nums = [int(current_sec_num)-i for i in range(1,int(current_gap))]
        possible_cor_nums = list(reversed(possible_cor_nums))


        prev_sec_rows = raw_df.loc[((raw_df["section_index"]==previous_sec_index) & (raw_df["chapter_index"]==current_chapter_index)), :].copy()
        prev_sec_rows['shift_text'] = prev_sec_rows.text.shift(-1)

        sec_matches = prev_sec_rows[(prev_sec_rows['text'].str.match(r'(S|s)[a-zA-Z]{1,3}(\.|,|:|;){0,2}$')==True) &
                                     (prev_sec_rows['shift_text'].str.match(r'[0-9.]+(\.|,|:|;){0,2}')==True)]

        for idx2, row in  sec_matches.iterrows():

            if previous_sec != row['text'] +' '+ row['shift_text']:

                num = get_nums_from_str(row['shift_text'])

                if num in possible_cor_nums:

                    sug_sec_title = row['text'] +' '+ str(num) + '.'
                    missing_sec_start_index = idx2
                    candidate_list.append({"sug_sec_title":sug_sec_title, 
                                        "missing_sec_start_index":missing_sec_start_index})



        if len(candidate_list) == 1 and len(possible_cor_nums) == 1:
            candidate_list[0]["sug_cor_sec_num"] = possible_cor_nums[0]
        elif len(candidate_list) > 1 and len(possible_cor_nums) == 1:
            for i in candidate_list:
                if str(possible_cor_nums[0]) in i["sug_sec_title"]:
                    i["sug_cor_sec_num"] = possible_cor_nums[0]
        elif len(candidate_list) == 1 and len(possible_cor_nums) > 1:
            for i in possible_cor_nums:
                if str(i) in candidate_list[0]["sug_sec_title"]:
                    candidate_list[0]["sug_cor_sec_num"] = i
        elif len(candidate_list) > 1 and len(possible_cor_nums) > 1:
            for i in candidate_list:
                for b in possible_cor_nums:
                    if str(b) in i["sug_sec_title"]:
                        i["sug_cor_sec_num"] = b

        for c in candidate_list:
            if "sug_cor_sec_num" in c:
                raw_df.loc[c["missing_sec_start_index"]:idx1-1, "section"] = c["sug_sec_title"]
                raw_df.loc[c["missing_sec_start_index"]:idx1-1, "raw_num"] = c["sug_cor_sec_num"]
                skip_fixes+=1
                fixes+=1


    raw_df["section_index"] = (raw_df.section != raw_df.section.shift(1)).groupby(raw_df.chapter).cumsum()
    sections = raw_df.loc[:, ['chapter', 'chapter_index', 'section', 'section_index']].drop_duplicates()
    sections['raw_num'] = sections['section'].apply(lambda x: 0 if x == "Chapter_Title" else (x.strip().split()[1].rstrip(punctuation) if " " in x.strip() and x.strip().split()[1].rstrip(punctuation).isnumeric() else np.nan))
    sections.loc[sections["section"]=="Paratextual", "raw_num"] = 0
    sections['raw_num'] = sections['raw_num'].astype(float)
    chapters = sections.groupby('chapter_index')
    sections["gap"] = chapters.raw_num.diff(1)



    #create new agg file
    agg = raw_df[raw_df["text"]!=""].groupby(['chapter', 'chapter_index', 'section', 'section_index'], sort=False)['text'].apply(' '.join).reset_index()

    #output new raw and agg files to .csv
    raw_outname = raw_file.replace("_cleaned_new.csv", "_round2.csv")
    raw_outname = raw_outname.replace("/chap_clean_raw_agg/raw_new/", "/sec_clean_test/raw/")
    agg_outname = raw_file.replace("_cleaned_new.csv", "_round2_agg.csv")
    agg_outname = agg_outname.replace("/chap_clean_raw_agg/raw_new/", "/sec_clean_test/agg/")
    #output new raw/agg to file
    raw_df.to_csv(raw_outname, index=False, encoding="utf-8")
    agg.to_csv(agg_outname, index=False, encoding="utf-8")


    # calculate statistics, compile report row dict
    gaps_remaining = sections['gap'].value_counts().keys().tolist()
    gap_counts = sections['gap'].value_counts().tolist()

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


    total_sections = sections.shape[0]+two_gaps_left+(2*three_gaps_left)
    total_errors = fixes+two_gaps_left+(2*three_gaps_left)+other_gaps_left
    if total_errors>0:
        percent_fixed = round((fixes/total_errors)*100, 2)
    else:
         percent_fixed = 100.00
    errors_remaining = two_gaps_left+(2*three_gaps_left)+other_gaps_left
    vol = os.path.basename(raw_file).replace("_data_cleaned_new.csv", "")

    # Compile "weird chaps" list for potentially easy manual fixes
    # these are chapters containing suspicious gaps
    weird_chaps = []
    for b in chapters.groups.keys():
            chap_sects = chapters.get_group(b)
            for r in range(0,chap_sects.shape[0]):
                if chap_sects.iloc[r]['gap'] > 3 or chap_sects.iloc[r]['gap'] < 1 or (chap_sects.iloc[r]['gap']==0 and chap_sects.iloc[r]['section_index']!=1):
                    for b in range(0,chap_sects.shape[0]):
                        weird_chaps.append({"vol":vol, 
                                                 "ch_index":chap_sects.iloc[b]['chapter_index'], 
                                                 "ch_title":chap_sects.iloc[b]['chapter'],
                                                 "sec_index":chap_sects.iloc[b]['section_index'],
                                                 "sec_title":chap_sects.iloc[b]['section'],
                                                 "gap":chap_sects.iloc[b]['gap']})
                    break
    
    total_weird_chaps = len(weird_chaps)

    # Generate dictionary to be added to corpus-level report
    report_row = {"vol":vol,
                  "total_sections":total_sections,
                  "total_errors":total_errors,
                  "total_fixes":fixes,
                  "percent_fixed":percent_fixed,
                  "errors_remaining":errors_remaining,
                  "non_numeric":non_numeric,
                  "external_refs":external_refs,
                  "south_sept":south_sept_fixes,
                  "lag3":lag3,
                  "lag2":lag2,
                  "lag1":lag1,
                  "weird_inserts":weird_inserts,
                  "one_two_eight":one_two_eight,
                  "three_eight_gaps":three_eight_gaps,
                  "skip_fixes":skip_fixes,
                  "weird_chaps": total_weird_chaps,
                  "weird_chaps_list": weird_chaps}


    return report_row


def main():
    # set path for directory containing raw files
    raw_path = r"C:\Users\npbyers\Desktop\OTB\SectNumFixes\chap_clean_raw_agg\raw_new"
    
    # create filepath list for all raw files in above directory
    rawfolder = "./chap_clean_raw_agg/raw_new/"
    raw_filelist = [(rawfolder + f) for f in os.listdir(raw_path) if f.endswith(".csv")]
    
    # run the 'run_fixes' function in parallel to minimize compute time
    # Generates new "raw" and "aggregate" ("agg") files for each volume
    # Compiles a list of all "report_row" dictionaries, one for each volume
    with joblib.parallel_backend(n_jobs=7,backend='loky'):
        report_rows = joblib.Parallel(verbose=5)(
        joblib.delayed(run_fixes)(raw_file) for raw_file in raw_filelist)    
    
    # create list of all sections for all chapters
    # containing sections with suspicious gaps
    # Convert list to dataframe and export to CSV for manual review
    weird_chap_master = []
    for row in report_rows:
        for i in row['weird_chaps_list']:
            weird_chap_master.append(i)
    weird_chap_df=pd.DataFrame(weird_chap_master)
    weird_chap_df.to_csv(r"C:\Users\npbyers\Desktop\OTB\SectNumFixes\weird_chaps.csv", index=False)
    weird_chap_df['vol'].value_counts()  

    # Create dataframe containing all automatic fix metadata for each volume
    # Export to .csv for manual review and future reference
    report_df=pd.DataFrame(report_rows)
    report_df = report_df.drop('weird_chaps_list', 1)
    report_df.to_csv(r"C:\Users\npbyers\Desktop\OTB\SectNumFixes\sec_clean_report.csv", index=False)
       
    
    
if __name__ == "__main__":
    main()