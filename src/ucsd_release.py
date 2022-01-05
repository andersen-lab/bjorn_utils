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
    variants_path = "variants/illumina/"
    report_path = "trimmed_bams/illumina/reports/"

    for path in [cons_path, bams_path, variants_path, report_path]:
        os.makedirs(os.path.join(dir_name, path))
    
    #define file endings
    variant_file_ending = "_L001_L002.tsv"
    consensus_file_ending = "_L001_L002.fa"
    bam_file_ending = "_L001_L002.sorted.bam"

    for row in range(len(data.index)):
        #TODO: Precalculate all the commands, add them to a list, and then have 10 processes work on them concurrently or something
        # get out the relevant info so we can use it on subprocess
        search_id = data.iloc[row, 0]
        variant_file_url = data.iloc[row, 1]
        consensus_file_url = data.iloc[row, 2]
        bam_file_url = data.iloc[row, 3]

        #TODO: Needs logging + multi-process, or to be called via boto3

        subprocess.run(
            ["aws", "s3", "cp", variant_file_url, os.path.join(dir_name, variants_path, "".join([search_id, variant_file_ending]))]
        )

        subprocess.run(
            ["aws", "s3", "cp", consensus_file_url, os.path.join(dir_name, cons_path, "".join([search_id, consensus_file_ending]))]
        )

        subprocess.run(
            ["aws", "s3", "cp", bam_file_url, os.path.join(dir_name, bams_path, "".join([search_id, bam_file_ending]))]
        )
    
    #TODO: Replace this with a pythonic equivalent
    os.chdir(os.path.join(dir_name, "consensus_sequences", "illumina"))
    replace_command = '''gawk -i inplace '/^>/{print ">Consensus_" substr(FILENAME,1,length(FILENAME)-3)"_threshold_0.5_quality_20"; next} 1' *.fa'''
    subprocess.call(replace_command, shell=True)

    os.chdir(os.path.join(dir_name, report_path))
    # get the files name without folder
    base_name = os.path.basename(sys.argv[1])
    report_file_url = os.path.join("s3://ucsd-all/phylogeny/", base_name.split(".")[0], base_name.split(".")[0] + ".full_summary.csv")
    subprocess.run(
        ["aws", "s3", "cp", report_file_url, os.path.join(dir_name, report_path, "full_summary.csv")]
        )
    summary = pd.read_csv("full_summary.csv")[["bam_name", "bjorn_coverage", "bjorn_avg_depth", "bjorn_min_coverage", "bjorn_max_coverage", "bjorn_num_w_zero_coverage"]]
    summary.rename(
        columns={
            "bjorn_coverage": "COVERAGE",
            "bjorn_avg_depth": "AVG_DEPTH",
            "bjorn_min_coverage": "MIN",
            "bjorn_max_coverage": "MAX",
            "bjorn_num_w_zero_coverage": "ZERO_DEPTH"},
            inplace=True
            )
    summary.dropna(inplace=True)
    summary["SAMPLE"] = [result[0]+"_L001_L002.trimmed.sorted.bam" for result in summary["bam_name"].str.split("__")]
    summary.drop(columns=["bam_name"], inplace=True)
    coverage_report = summary[["SAMPLE", "COVERAGE", "AVG_DEPTH", "MIN", "MAX", "ZERO_DEPTH"]]
    coverage_report.to_csv("coverage_report.tsv", index=False, sep="\t")
