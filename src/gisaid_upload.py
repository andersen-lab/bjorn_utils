"""
Overarching infrastructure to facilitate uploads to gisaid, github, and google
cloud storage Current implementation requires specific pre-install of all
dependencies but future version will include automated installation and
configuration utils
"""

import os
import sys

import pandas as pd

def merge_gisaid_ids(gisaid_log_file: str = "/home/al/code/gisaid_uploader.log", metadata_path: str = "/home/al/code/HCoV-19-Genomics/metadata.csv") -> None:
    """
    Takes a log file and uses the returned gisaid ids to update the metadata
    stored in the HCoV-19-Genomics repository - can be modified to update other
    metadata files in future iterations 
    """
    with open(gisaid_log_file, 'r') as infile:
        # reads all the lines from the log minus the last two which are not in the same format
        lines = infile.readlines()[:-2]
    # get the first column, which are our own ids again
    column_1 = [element.split(";")[0] for element in lines]
    # get the second column, which are gisaid ids
    column_2 = [element.split(";")[1].strip("\n") for element in lines]
    # generate a dataframe with these two columns
    df = pd.DataFrame(list(zip(column_2, column_1)), columns =['gisaid_accession', 'fasta_hdr'])
    # read metadata file
    metadata = pd.read_csv(metadata_path)
