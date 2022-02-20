"""
Replaces separate bash concatenation, unalignment, and multifasta to fasta
commands with a single pythonic interface

Can either be called from command line directly as a cohesive package or as
separate package elements
"""

from cgi import test
from curses import meta
from datetime import date
from logging import raiseExceptions
import os
import sys
from Bio import SeqIO
import pandas as pd
import subprocess
from readme_update import main as readme_main
from gsheet_interact import gisaid_interactor, zipcode_interactor


def merge_gisaid_ids(gisaid_log_file: str = "/home/al/code/bjorn_utils/src/gisaid_uploader.log", metadata_path: str = "/home/al/code/HCoV-19-Genomics/metadata.csv") -> None:
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

def merge_zipcodes(local_file_path: str = "", metadata_path: str = "/home/al/code/HCoV-19-Genomics/metadata.csv", config_key_path: str = "/home/al/code/bjorn_utils/bjorn.ini") -> None:
    """
    Takes a log file and uses the returned gisaid ids to update the metadata
    stored in the HCoV-19-Genomics repository - can be modified to update other
    metadata files in future iterations 
    """
    # generate a dataframe with these two columns
    if local_file_path == "" :
        df = zipcode_interactor(config_key_path).rename(
            columns={"Zipcode": "zipcode", "SEARCH SampleID": "ID"}).drop_duplicates()
    else:
        df = pd.read_csv(local_file_path).rename(columns={"Additional location information": "zipcode", "SEARCH SampleID": "ID"})[["zipcode", "ID"]].drop_duplicates()
    # read metadata file
    metadata = pd.read_csv(metadata_path)
    column_order = metadata.columns.to_list()
    # sort for the metadata where gisaid_id is missing
    missing_zipcodes = metadata[metadata["zipcode"].isna()].drop(columns=["zipcode"])
    not_missing_zipcode = metadata[~metadata["zipcode"].isna()]
    # merge data
    merged = missing_zipcodes.merge(df, how='left', on="ID")
    # reset column order and return
    new_metadata = pd.concat([not_missing_zipcode, merged[column_order]])
    # write new_metadata to disk
    new_metadata.to_csv(metadata_path, index=False)
    return

def merge_hosts(local_file_path: str = "", metadata_path: str = "/home/al/code/HCoV-19-Genomics/metadata.csv", config_key_path: str = "/home/al/code/bjorn_utils/bjorn.ini") -> None:
    """
    Takes a log file and uses the returned gisaid ids to update the metadata
    stored in the HCoV-19-Genomics repository - can be modified to update other
    metadata files in future iterations 
    """
    # generate a dataframe with these two columns
    if local_file_path == "" :
        df = gisaid_interactor(config_key_path).rename(
            columns={"Host": "host", "SEARCH SampleID": "ID"})[["host", "ID"]].drop_duplicates()
    else:
        df = pd.read_csv(local_file_path).rename(columns={"Host": "host", "SEARCH SampleID": "ID"})[["host", "ID"]].drop_duplicates()
    # read metadata file
    metadata = pd.read_csv(metadata_path)
    column_order = metadata.columns.to_list()
    # sort for the metadata where gisaid_id is missing
    missing_host = metadata[metadata["host"].isna()].drop(columns=["host"])
    not_missing_host = metadata[~metadata["host"].isna()]
    # merge data
    merged = missing_host.merge(df, how='left', on="ID")
    # reset column order and return
    new_metadata = pd.concat([not_missing_host, merged[column_order]])
    # write new_metadata to disk
    new_metadata.to_csv(metadata_path, index=False)
    return


def concat_fastas(file_1: str, file_2: str, combined_aligned_fasta: str) -> None:
    """
    Concatenates a two files into a combined fasta format
    """
    with open(combined_aligned_fasta, "w") as outfile:
        for fname in [file_1, file_2]:
            with open(fname, "r") as infile:
                for line in infile:
                    outfile.write(line)
    return

def unalign_fasta(combined_aligned_fasta: str, combined_unaligned_fasta: str) -> None:
    """
    Takes an aligned fasta and writes an unaligned fasta to the same directory
    """
    # if the line starts with a > (fasta header) print that line
    # else substitute "-" with nothing
    with open(combined_unaligned_fasta, "w") as outfile:
        with open(combined_aligned_fasta, "r") as infile:
            for line in infile:
                if line[0] == ">":
                    outfile.write(line)
                else:
                    outfile.write(line.replace("-", ""))
    return

def multifasta_to_fasta(combined_unaligned_fasta: str) -> None:
    """
    Takes a combined fasta and splits it into separate files in a "consensus
    sequences" folder within the main directory
    """
    # create new directory for consensus sequences
    base_dir = os.path.dirname(combined_unaligned_fasta)
    cons_dir = os.path.join(base_dir, "consensus_sequences")
    if not os.path.exists(cons_dir):
        os.mkdir(cons_dir)
    # generate a separated fasta file for each sequence
    failed_sequences = []
    with open(combined_unaligned_fasta, "r") as infile:
        records = SeqIO.parse(infile, "fasta")
        for record in records:
            try:
                file_path = os.path.join(cons_dir, record.id.split("/")[2] + ".fasta")
                with open(file_path, "w") as outfile:
                    outfile.writelines(SeqIO.FastaIO.as_fasta_2line(record))
            except IndexError:
                failed_sequences.append(record.id)
    return failed_sequences

def _get_fasta_true_name(header: str) -> str:
    """
    Take a header line which is supposed to be a fasta name and then get the
    true name without any '/' or '>'
    """
    if "/" in header:
        return header.split("/")[2]
    else:
        return header[1:]


if __name__ == "__main__":
    # generate files from folder pattern
    """
    Takes only 1 required argument, which is the bjorn generated folder
    Second argument can be the location of the metadata file from which to pull zipcodes
    #TODO: Allow this to take location of the HCoV-19-Genomics folder as an argument throughout
    """
    white_fasta = os.path.join(sys.argv[1], "msa", sys.argv[1].split("/")[2] + "_aligned_white.fa")
    inspect_fasta = os.path.join(sys.argv[1], "msa", sys.argv[1].split("/")[2] + "_aligned_inspect.fa")
    combined_aligned_fasta = os.path.join(sys.argv[1], "msa", sys.argv[1].split("/")[2] + "_combined_aligned.fa")
    combined_unaligned_fasta = os.path.join(sys.argv[1], "msa", sys.argv[1].split("/")[2] + "_combined_unaligned.fa")
    
    # concat, unalign, and multifasta to fasta consensus sequences
    concat_fastas(white_fasta, inspect_fasta, combined_aligned_fasta)
    unalign_fasta(combined_aligned_fasta, combined_unaligned_fasta)
    multifasta_to_fasta(combined_unaligned_fasta)

    # upload to gisaid using the metadata in the folder and get the logs
    #TODO: Add some kind of logging that allows us to understand what we have done so far for a bjorn folder
    gisaid_fasta = combined_unaligned_fasta
    gisaid_metadata = os.path.join(sys.argv[1], "gisaid_metadata.csv")

    # check Pangolin lineage timings for the current set of sequences
    subprocess.run(["./update_pangolineages_subset.sh", os.path.join(sys.argv[1], "msa")])
    lineage_report = pd.read_csv(os.path.join(sys.argv[1], "msa", "lineage_report.csv"))[['taxon', "scorpio_call"]]
    metadata_reduced = pd.read_csv(gisaid_metadata)[["covv_virus_name", "covv_collection_date"]] 
    metadata_reduced["taxon"] = [item.split("/")[2] for item in metadata_reduced["covv_virus_name"]]
    meta_lineage_merge = metadata_reduced.merge(lineage_report, how="left", on="taxon")
    pango_df = pd.read_csv("../lineage_reference.csv")
    meta_lineage_reference_merge = meta_lineage_merge.merge(pango_df, how="left", on="scorpio_call")
    meta_lineage_reference_merge["reference_date"] = pd.to_datetime(meta_lineage_reference_merge["reference_date"])
    meta_lineage_reference_merge["covv_collection_date"] = pd.to_datetime(meta_lineage_reference_merge["covv_collection_date"])
    test_frame = meta_lineage_reference_merge[meta_lineage_reference_merge["covv_collection_date"] < meta_lineage_reference_merge["reference_date"]]
    if len(test_frame) > 0:
        print(test_frame)
        raise Exception("Error: lineage appears before reference start date - check metadata and sequences")

    # now that pangolin checks are complete, we can start gisaid upload
    # actual gisaid upload
    gisaid_failed_metadata = os.path.join(sys.argv[1], "gisaid_failed_metadata.csv")
    subprocess.run(["./gisaid_uploader", 
                    "CoV", 
                    "upload", 
                    "--fasta", 
                    gisaid_fasta,
                    "--csv" ,
                    gisaid_metadata, 
                    "--failedout", 
                    gisaid_failed_metadata]
                )

    # kick off gsutil upload
    subprocess.run(["./gsutil_uploader.sh", sys.argv[1]])

    # use gisaid metadata to update the github metadata
    merge_gisaid_ids()

    # merge zipcode data
    if len(sys.argv) == 3:
        merge_zipcodes(local_file_path=sys.argv[2])
    elif len(sys.argv) == 2:
        merge_zipcodes()
    else:
        raise Exception("Merge zipcodes received incorrect number of arguments")

    # merge host data
    if len(sys.argv) == 3:
        merge_hosts(local_file_path=sys.argv[2])
    elif len(sys.argv) == 2:
        merge_hosts()
    else:
        raise Exception("Merge hosts received incorrect number of arguments")

    #TODO: Run pangolin on the whole dataset here vs separately in the pangolin script
    subprocess.run(["./update_pangolineages.sh"])

    # Push changes to the github repo
    subprocess.run(["./push_git_changes.sh"])

    #TODO: Fix errors here
    # update the readme in the github folder
    # readme_main("/home/al/code/HCoV-19-Genomics/")
