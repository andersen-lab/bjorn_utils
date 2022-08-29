"""
Basic utils for manipulation of ONT processing files
Used during ONT pipeline runs
"""

from hashlib import new
import sys
import os
import glob
import shutil


def folder_cleanup(path: str) -> None:
    """
    Takes all fasta files created after barcoding and
    adds them to their own folder so guppy works as expected

    Does not automatically traverse down into the demultiplexed folder
    for now
    """
    # take the file path and get the list of fastq files there
    list_of_fastqs = glob.glob(os.path.join(path, "*.fastq"))
    # loop over list of fastq
    for fastq in list_of_fastqs:
        # create a new folder for each fastq
        fastq_file_name = os.path.basename(fastq).split(".")[0]
        new_folder_path = os.path.join(path, fastq_file_name)
        os.mkdir(new_folder_path)
        # move the fastq file into that folder
        shutil.move(fastq, os.path.join(new_folder_path, fastq_file_name + ".fastq"))
