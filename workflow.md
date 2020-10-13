# *OnTheBooks* Workflow
This page is meant to provide an overview of the workflow used to create the On the Books corpus. The workflow can be divided into seven major stages:

1. Data Acquisition
2. Marginalia Determination
3. Image Adjustment Recommendations
4. Optical Character Recognition (OCR)
5. Section Splitting & Cleaning
6. Analysis
7. XML Generation

## Data Acquisition
During data acquisition, images and metadata were gathered through a combination of automatic downloads from the Internet Archive and manual metadata creation.

First, digitized versions of the volumes from the Internet Archive were identified using the Internet Archive's advanced search interface. Using the metadata that resulted from this search, all images comprising the corpus were downloaded using [jp2_download.py](https://github.com/UNC-Libraries-data/OnTheBooks/blob/master/code/data_acquisition/jp2_download.py). Extraneous page images, such as blank pages or those containing tables of contents, were manually identified and deleted.

Next, metadata such as law type (private laws, public laws, etc.) and original print page number were manually compiled for corpus images. These metadata were combined with other page-level metadata such as the leaf number (pdf page number) and page hand side (left or right), gathered from Internet Archive XML files using [xml_parser.py](https://github.com/UNC-Libraries-data/OnTheBooks/blob/master/code/data_acquisition/xml_parser.py).

The products of this stage consisted of a curated set of all relevant image files as well as page-level metadata for all images in the corpus:
* file name
* leaf number
* hand side
* print page number
* law type section
* law type section title
* Internet Archive image URL

These items were compiled into a corpus-level document called 'xmljpegmerge.csv'.

**Output File(s):**
* *xmljpegmerge.csv* - .csv file with page-level metadata for the entire corpus

## Marginalia Determination
Marginalia, which is text that serves as a finding aid, was printed in the corpus volumes prior to 1951. The marginalia are not part of the laws and needed to be left out of the OCR process, as did paratextual information from page headers and footers. The marginalia determination process involved identifying the coordinates of the main text body for OCR. The marginalia determination process also identified the median page color to allow for the creation of a blank, color-neutral border around the main body text on each page. Tesseract OCR performs best when the text is not too close to the edge of the page.

This step was accomplished using [marginalia_determination.py](https://github.com/UNC-Libraries-data/OnTheBooks/blob/master/code/marginalia/marginalia_determination.py) in concert with [cropfunctions.py](https://github.com/UNC-Libraries-data/OnTheBooks/blob/master/code/marginalia/cropfunctions.py). Detailed documentation for this step can be found [here](https://github.com/UNC-Libraries-data/OnTheBooks/blob/master/examples/marginalia_determination/marginalia_determination.ipynb).

**Output File(s):**
* *marginalia_metadata.csv* - .csv file containing main body text boundary coordinates and background color information for each page in the corpus

## Image Adjustment Recommendations
Once the marginalia cropping information had been compiled, various image adjustments were tested for each volume to maximize OCR performance. A sample of images for each volume was selected and tested using different values for a range of parameters (color, contrast, etc.). Once the optimal image adjustments for each volume had been determined, these were stored for use during the following OCR stage.

This step was accomplished using [adjRec.py](https://github.com/UNC-Libraries-data/OnTheBooks/blob/master/code/ocr/adjRec.py) in concert with [ocr_func.py](https://github.com/UNC-Libraries-data/OnTheBooks/blob/master/code/ocr/ocr_func.py). Detailed documentation for this step can be found [here](https://github.com/UNC-Libraries-data/OnTheBooks/blob/master/examples/adjustment_recommendation/adjRec.ipynb).

**Output File(s):**
* *adjustments.csv* - .csv file containing OCR-optimized image adjustment parameter values for each volume

## Optical Character Recognition (OCR)
Having produced the prerequisite files ("adjustments.csv", "marginalia_metadata.csv", and "xmljpegmerge.csv"), OCR was performed on each page of each volume to produce a series of output files. OCR output files were saved for each law type (public, private, public-local) and session (e.g. Private Laws of the State of North Carolina, Session 1891 saved as lawsresolutionso1891nort_private laws_data.tsv).

This step was accomplished using [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki), which was accessed programmatically via a [pytesseract](https://pypi.org/project/pytesseract/) wrapper. The scripts involved in this stage were [ocr_use.py](https://github.com/UNC-Libraries-data/OnTheBooks/blob/master/code/ocr/ocr_use.py) and those functions contained in [ocr_func.py](https://github.com/UNC-Libraries-data/OnTheBooks/blob/master/code/ocr/ocr_func.py). Detailed documentation for this step can be found [here](https://github.com/UNC-Libraries-data/OnTheBooks/blob/master/examples/ocr/ocr_use.ipynb).

**Output File(s):**
* *(volume)_adjustments.txt* - stores the image adjustments used to perform OCR on that particular volume. One of these files was created for each physical volume.
* *(volume)_(section).txt* - stores a compiled version of all OCR'd text for a given law type section. One of these files was created for each set of laws ("Public", "Private", etc.) found in each physical volume.
* *(volume)_(section)_data.tsv* - a word-level .tsv file for a given section. The rows in this file correspond to each individual token (word) recorded by the OCR process, along with page coordinates and confidence value for each. One of these files was created for each set of laws ("Public", "Private", etc.) in each physical volume.

## Section Splitting & Cleaning
After completing OCR, each volume was 'split' into its constituent chapters and sections, with each section representing an individual law. This was accomplished using regular expression pattern matching on the word-level "(volume)_(section)_data.tsv" files produced in the previous step. Once initial assignments had been made, the corpus underwent a lengthy cleaning process that eliminated most section and chapter assignment errors and created a set of "aggregate" files in which all words were aggregated into their assigned sections (laws).

This step was accomplished using the 7 separate scripts located [here](https://github.com/UNC-Libraries-data/OnTheBooks/tree/master/code/split_cleanup) in combination with several rounds of manual review. Detailed documentation for this step can be found [here](https://github.com/UNC-Libraries-data/OnTheBooks/blob/master/examples/split_cleanup/split_cleanup.ipynb).

**Output File(s):**
* *(volume)_(section)_data.csv* - an updated version of the 'raw' output .tsv files created in the OCR step. One of these files was created for each set of laws found ("Public", "Private", etc.) in each physical volume.
* *(volume)_(section)_aggregate_data.csv* - contains all volume text aggregated into sections (laws). One of these files was created for each set of laws found ("Public", "Private", etc.) in each physical volume.

## Analysis
The analysis phase of the project involved both supervised and unsupervised learning methods. The purposes of this phase were twofold:
1. To use automated techniques to help explore and better understand the characteristics and composition of Jim Crow Laws
2. To provide an efficient means for expanding the collection of Jim Crow laws already identified by experts

This phase utilized the aggregated versions of the laws, compiled during the previous phase: "(volume)_(section)_aggregate_data.csv".

Latent Dirichlet Allocation, an unsupervised method, was used to build a topic model for the laws. This analysis was conducted by team member Rucha Dalwadi and is detailed in her master’s paper ([Dalwadi 2020](https://doi.org/10.17615/tksc-t217)).

Following the unsupervised classification efforts, an effort was made to identify Jim Crow laws using "active" supervised classification. A training set was compiled by expert reviewers doing close reading. A combination of preliminary classification runs and expert review was used to expand the existing labeled training set. The resulting expanded training set was used to [perform classification on the entire corpus](https://unc-libraries-data.github.io/OnTheBooks/code/classification/Model_Aug2020.html). This allowed for the labeling of laws as "Jim Crow" or "not Jim Crow" based on a pre-determined probability threshold.

This step was accomplished using [scikit learn](https://scikit-learn.org/) and [XGBoost](https://xgboost.readthedocs.io/) to build and evaluate models. For text processing, [nltk](https://www.nltk.org/) was used.

**Output File(s):**
* *jim_crow_list.csv* - contains all laws identified as Jim Crow laws by expert reviewers, analytical models, or both.
* *law_list.csv* - contains all laws in the corpus with all metadata accumulated from previous steps along with each law's Jim Crow classification value and classification source (experts, models, or both).

## XML Generation
Following the analysis phase, the corpus was prepared for dissemination from the [Carolina Digital Repository](https://doi.org/10.17615/5c4g-sd44). Each volume was enriched with metadata as XML. Metadata files were merged using a unique identifier, then added to the corpus as XML elements and attributes. Python's [ElementTree](https://docs.python.org/3/library/xml.etree.elementtree.html) API was used to generate the XML. A .xsd schema was then created that defines the information provided about each volume in the corpus, such as the volume title, year, and session name. The schema also provides information about the laws contained in each volume, such as law titles, types, and Jim Crow classifications.

**Output File(s):**
* *onthebooks.xsd* - the xml schema definition for all xml files in the corpus.
* *(volume).xml* - contains metadata and content for all laws within a given volume, tagged according to the above schema. One of these files was created for each physical volume in the corpus.
