from posixpath import dirname
import pandas as pd
import os
import subprocess
import sys

from pandas.core.reshape.merge import merge_ordered

if __name__=="__main__":
    """
    Takes a given folder which contains UCSD data, and
    the csv report within that folder and starts generating an
    output usable by bjorn
    """
    # read in the data file
    data = pd.read_csv(sys.argv[1])[
        ["SEARCH SampleID", "Variant File S3 URL", "Consensus File S3 URL", "BAM File S3 URL"]
        ]
    
    # get the directory name and cd into it
    dir_name = os.path.dirname(sys.argv[1])
    
    # make the folders we need, no error if they already exist
    cons_path = "consensus_sequences/illumina/"
    bams_path = "merged_aligned_bams/illumina/"
    variants_path = "variants/illumina/reports/"
    report_path = "trimmed_bams/illumina/reports/"

    for path in [cons_path, bams_path, variants_path, report_path]:
        os.makedirs(os.path.join(dir_name, path))
    
    #define file endings
    variant_file_ending = "_L001_L002.tsv"
    consensus_file_ending = "_L001_L002.fa "
    bam_file_ending = "_L001_L002.sorted.bam"

    for row in range(len(data.index)):
        # get out the relevant info so we can use it on subprocess
        search_id = data.iloc[row, 0]
        variant_file_url = data.iloc[row, 1]
        consensus_file_url = data.iloc[row, 2]
        bam_file_url = data.iloc[row, 3]

        subprocess.run(
            ["aws", "s3", "cp", variant_file_url, os.path.join(dir_name, variants_path, "".join([search_id, variant_file_ending]))]
        )

        subprocess.run(
            ["aws", "s3", "cp", consensus_file_url, os.path.join(dir_name, cons_path, "".join([search_id, consensus_file_ending]))]
        )

        subprocess.run(
            ["aws", "s3", "cp", bam_file_url, os.path.join(dir_name, bams_path, "".join([search_id, bam_file_ending]))]
        )

    # get the summary file last and put it in the reports path
