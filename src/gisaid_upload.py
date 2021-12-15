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
    column_order = metadata.columns.to_list()
    # sort for the metadata where gisaid_id is missing
    missing_gisaid_id = metadata[metadata["gisaid_accession"].isna()].drop(columns=["gisaid_accession"])
    not_missing_gisaid_id = metadata[~metadata["gisaid_accession"].isna()]
    # merge data
    merged = missing_gisaid_id.merge(df, how='left', on='fasta_hdr')
    # reset column order and return
    new_metadata = pd.concat([not_missing_gisaid_id, merged[column_order]])
    # write new_metadata to disk
    new_metadata.to_csv(metadata_path, index=False)
    return