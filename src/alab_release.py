import pandas as pd
from path import Path
from shutil import copy, move
from Bio import SeqIO
import argparse
import glob
import subprocess
from multiprocessing import Pool
from itertools import repeat
import os
import bjorn_support as bs
import mutations as bm
import json


def create_gisaid_meta(new_meta_df: pd.DataFrame, meta_cols: list):
    """Generate GISAID metadata for newly released samples"""
    na_cols = ['covv_gender','covv_patient_age','covv_patient_status', 'covv_sampling_strategy', "covv_comment", "comment_type"]
    new_meta_df.loc[:, na_cols] = new_meta_df[na_cols].fillna('N/A')
    new_meta_df['covv_coverage'] = new_meta_df['avg_depth'].copy()
    new_meta_df.drop(columns=['avg_depth'], inplace=True)
    new_meta_df['covv_assembly_method'] = 'iVar 1.3.1'
    new_meta_df['submitter'] = 'mzeller'
    # note that an added benefit of this method is that it should reorder the columns for us
    new_meta_df[meta_cols].to_csv(out_dir/'gisaid_metadata.csv', index=False)
    return new_meta_df


def get_ids(filepaths: list) -> list:
    "Utility function to get a unified sample ID format from the analysis file paths"
    ids = []
    for fp in filepaths:
        # query = fp.basename().split('-')
        n = fp.basename()
        if n[:6] != "SEARCH":
            n = n[n.find("SEARCH"):]
        query = n.split('_')[0].split('-')
        if len(query) > 1:
            ids.append(''.join(query[:2]))
        else:
            start_idx = fp.find('SEARCH')
            ids.append(fp[start_idx:start_idx+10])
    return ids


def process_coverage_sample_ids(x):
    "Utility function to get a unified sample ID format from the coverage reports"
    if x[:6] != "SEARCH":
        x = x[x.find("SEARCH"):]
    query = x.split('/')
    if len(query) == 1:
        return ''.join(x.split("_")[0].split('-')[:2]) # Format could be SEARCH-xxxx-LOC or SEARCH-xxxx
    else:
        start_idx = x.find('SEARCH')
        return x[start_idx:start_idx+10] # SEARCHxxxx

def retransfer_files(filepaths: pd.DataFrame, destination: str, suspicious_sample_ids: list, include_bams: bool=False, ncpus: int=1):
    """Utility function to separate the consensus and BAM files of samples containing suspicious 
    INDELs and/or substitutions from the remaining white-listed samples."""
    # FASTA and filepaths for samples that require manual inspection prior to public release
    inspect_filepaths = filepaths.loc[filepaths['fasta_hdr'].isin(suspicious_sample_ids)][['PATH_x', 'PATH_y']]
    # FASTA and BAM filepaths for samples that are ready for public release (white-listed samples)
    white_filepaths = filepaths.loc[~filepaths['fasta_hdr'].isin(suspicious_sample_ids)][['PATH_x', 'PATH_y']]
    # create respective directories
    if not Path.isdir(destination):
        Path.mkdir(destination)
    if not Path.isdir(destination/'fa_white/'):
        Path.mkdir(destination/'fa_white/')
    if not Path.isdir(destination/'fa_inspect/'):
        Path.mkdir(destination/'fa_inspect/')
    if not Path.isdir(destination/'bam_white/'):
        Path.mkdir(destination/'bam_white/')
    if not Path.isdir(destination/'bam_inspect/'):
        Path.mkdir(destination/'bam_inspect/')
    # re-locate sample files to their respective whitelist or inspect folders
    with Pool(ncpus) as pool:
        # move FASTA files of white-listed samples into their respective folder
        res = pool.starmap(move_files, zip(repeat(destination/'fa'),
                                           repeat(destination/'fa_white'), 
                                           white_filepaths['PATH_x'].tolist()))
        # move FASTA files of black-listed samples into their respective folder
        res = pool.starmap(move_files, zip(repeat(destination/'fa'),
                                           repeat(destination/'fa_inspect'),
                                           inspect_filepaths['PATH_x'].tolist()))
        if include_bams:
            # move BAM files of white-listed samples into their respective folder
            res = pool.starmap(move_files, zip(repeat(destination/'bam'),
                                               repeat(destination/'bam_white'),
                                               white_filepaths['PATH_y'].tolist()))
            # move BAM files of black-listed samples into their respective folder
            res = pool.starmap(move_files, zip(repeat(destination/'bam'),
                                               repeat(destination/'bam_inspect'), 
                                               inspect_filepaths['PATH_y'].tolist()))
        pool.close()
        pool.join()
    return 0


def move_files(in_dir, out_dir, original_filepath):
    # filepath before moving
    current_filepath = os.path.join(in_dir, os.path.basename(original_filepath))
    # filepath after moving (tentatively)
    new_filepath = os.path.join(out_dir, os.path.basename(original_filepath))
    # if file already there, ignore move operation
    if Path.isfile(Path(new_filepath)): return 0
    print(f"Transferring {current_filepath} to {new_filepath}")
    try: move(current_filepath, new_filepath)
    except: return f"File {current_filepath} not found. Ignoring move operation"
    return 0


def transfer_files(filepaths: pd.DataFrame, destination: str, include_bams=False, ncpus = 1):
    "Utility function to copy consensus and BAM files of given samples from source to destination"
    filepaths = filepaths[['PATH_x', 'PATH_y', "Virus name"]]
    destination = Path(destination)
    if not Path.isdir(destination):
        Path.mkdir(destination)
    if not Path.isdir(destination/'fa/'):
        Path.mkdir(destination/'fa/')
    if not Path.isdir(destination/'bam/'):
        Path.mkdir(destination/'bam/')
    with Pool(ncpus) as pool:
        res = pool.starmap(transfer_cns_sequence,
                           zip(repeat(destination/"fa/"),
                               filepaths["PATH_x"].tolist(), filepaths["Virus name"].tolist()))
        if include_bams:
            res = pool.starmap(transfer_bam, zip(repeat(destination/"bam/"),
                                                 filepaths["PATH_y"].tolist()))
        pool.close()
        pool.join()
    return 0


def transfer_bam(out, bam_fp):
    n = os.path.join(out, os.path.basename(bam_fp))
    if Path.isfile(Path(n)): return 0
    print("Transferring {} to {}".format(bam_fp, n))
    out = subprocess.Popen(["samtools", "view", "-b", "-F", "4", "-o", n, bam_fp],
                           stdout = subprocess.PIPE,
                           stderr = subprocess.PIPE, shell=False)
    stdout, stderr = out.communicate()
    if len(stderr) !=0:
        print(stderr)
    return 0

def transfer_cns_sequence(out, cons_fp, virus_name):
    n = os.path.join(out, os.path.basename(cons_fp))
    if Path.isfile(Path(n)): return 0
    print("Transferring {} to {}".format(cons_fp, n))
    rec = SeqIO.read(cons_fp, format="fasta")
    new_cns_name = virus_name
    rec.name = new_cns_name
    rec.id = new_cns_name
    rec.description = new_cns_name
    with open(n, "w") as fout:
        SeqIO.write(rec, fout, format="fasta")
        fout.close()
    return 0

def process_id(x):
    "Utility function to process sample IDs to fix inconsistencies in the format"
    return ''.join(x.split('-')[:2])

if __name__=="__main__":
    # Input Parameters
    # COLUMNS TO INCLUDE IN GISAID METADATA
    gisaid_meta_cols = [
        'submitter', 'fn', 'covv_virus_name', 'covv_type', 'covv_passage', 'covv_collection_date', 
        'covv_location', 'covv_add_location','covv_host', 'covv_add_host_info', 'covv_sampling_strategy', 'covv_gender', 
        'covv_patient_age', 'covv_patient_status', 'covv_specimen', 'covv_outbreak', 'covv_last_vaccinated', 'covv_treatment', 
        'covv_seq_technology', 'covv_assembly_method', 'covv_coverage', 'covv_orig_lab', 'covv_orig_lab_addr', 'covv_provider_sample_id', 
        'covv_subm_lab', 'covv_subm_lab_addr', 'covv_subm_sample_id', 'covv_authors', 'covv_comment', 'comment_type'
        ]
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', "--not-dry-run", action='store_false', help="Dry run. Default: True")

    parser.add_argument("-b", "--include-bams", action='store_true', help="Whether or not to include BAM files in the release")

    parser.add_argument("-r", "--reference",
                        type=str,
                        default="/home/gk/code/hCoV19/db/NC045512.fasta",
                        help="Reference to use")

    parser.add_argument("-rn", "--reference-name",
                        type=str,
                        default="NC_045512.2",
                        help="FASTA header name for reference")

    parser.add_argument("-mc", "--min-coverage",
                        type=int,
                        default=95,
                        help="Minimum coverage of sequences (QC filter)")
    
    parser.add_argument("-md", "--min-depth",
                        type=int,
                        default=1000,
                        help="Minimum depth of sequences (QC filter)")

    parser.add_argument("-o", "--out-dir",
                        type=str,
                        default="./",
                        help="Output directory")

    parser.add_argument("-n", "--cpus",
                        type=int,
                        default=1,
                        help="Number of cpus to use")

    parser.add_argument("-s", "--sample-sheet",
                        type=str,
                        required=True,
                        help="Sample sheet to use. Please make sure it is the most recent")

    parser.add_argument("-a", "--analysis-folder",
                        type=str,
                        required=True,
                        help="Path to the analysis folder that contains all the files")

    parser.add_argument("-m", "--output-metadata",
                        type=str,
                        required=True,
                        help="Output csv for metadata of the released samples")
    args = parser.parse_args()

    # whether or not to include bam files in the release
    include_bams = args.include_bams
    # this is the minimum coverage for accepting consensus sequences
    min_coverage = args.min_coverage
    # this is the minimum average depth (per nucleotide position) for accepting consensus sequences
    min_depth = args.min_depth
    # path to reference sequence (used later for MSA and tree construction)
    ref_path = Path(args.reference) if args.reference is not None else None
    patient_zero = args.reference_name
    # this is the directory where results get saved
    out_dir = Path(args.out_dir)
    # number of cores to use
    num_cpus = args.cpus
    # file path to samples sheet (make sure it is the most recent)
    sample_sheet_fpath = args.sample_sheet
    # path to analysis results
    analysis_fpath = args.analysis_folder
    # file path to metadata of samples that have already been released
    released_samples_fpath = args.output_metadata
    # Whether run is dry
    dry_run = args.not_dry_run

    print(f"""User Specified Parameters:
    Dry run: {dry_run}.
    Include BAMS: {include_bams}.
    Reading release summary file from {sample_sheet_fpath}.
    Reading repository metadata from {released_samples_fpath}.
    Searching analysis folder {analysis_fpath}.
    """
    )

    # Collecting Sequence Data
    # grab all filepaths for bam data
    bam_filepaths = bs.get_filepaths(analysis_fpath, data_fmt='bam', 
                                     data_type='merged_aligned_bams', 
                                     tech='illumina',
                                     generalised=True,
                                     return_type='list')
    # print(bam_filepaths)
    # bam_filepaths = glob.glob(f"{analysis_fpath}/**/merged_aligned_bams/illumina/*.bam")
    bam_filepaths = [Path(fp) for fp in bam_filepaths]
    # consolidate sample ID format
    bam_ids = get_ids(bam_filepaths)
    # Turn into dataframe
    bam_data = list(zip(*[bam_ids, bam_filepaths]))
    bam_df = pd.DataFrame(data=bam_data, columns=['sample_id', 'PATH'])
    # grab all paths to consensus sequences
    # grab all filepaths for bam data
    consensus_filepaths = bs.get_filepaths(analysis_fpath, data_fmt='fa', 
                                     data_type='consensus_sequences', 
                                     tech='illumina',
                                     generalised=True,
                                     return_type='list')
    consensus_filepaths = [Path(fp) for fp in consensus_filepaths]
    # consolidate sample ID format
    consensus_ids = get_ids(consensus_filepaths)
    # Turn into dataframe
    consensus_data = list(zip(*[consensus_ids, consensus_filepaths]))
    consensus_df = pd.DataFrame(data=consensus_data, columns=['sample_id', 'PATH'])
    # clean up cns and bam (remove duplicate IDs)
    bam_df.drop_duplicates(subset=['sample_id'], keep='last', inplace=True)
    consensus_df.drop_duplicates(subset=['sample_id'], keep='last', inplace=True)
    # include only SEARCH samples
    consensus_df = consensus_df[(consensus_df['sample_id'].str.contains('SEARCH'))]
    # merge consensus and bam filepaths for each sample ID
    analysis_df = pd.merge(consensus_df, bam_df, on='sample_id', how='left')
    #TODO: Make this download the latest version directly from google
    # load sample sheet data (GISAID) - make sure to download most recent one
    seqsum = pd.read_csv(sample_sheet_fpath)
    # clean up
    seqsum = seqsum[(~seqsum['SEARCH SampleID'].isna()) & (seqsum['SEARCH SampleID']!='#REF!')]
    # consolidate sample ID format
    seqsum.loc[:, 'sample_id'] = seqsum['SEARCH SampleID'].apply(process_id)
    seqsum.drop_duplicates(subset=['sample_id'], keep='last', inplace=True)
    seqsum = seqsum[seqsum['New sequences ready for release'] == 'Yes']
    num_seqs_to_release = seqsum['sample_id'].unique().shape[0]
    # JOIN summary sheet with analysis meta data
    sequence_results = pd.merge(seqsum, analysis_df, on='sample_id', how='inner')
    # compute number of samples with missing consensus and/or bam files
    num_seqs_found = sequence_results['sample_id'].unique().shape[0]
    num_samples_missing_cons = num_seqs_to_release - num_seqs_found
    num_samples_missing_bams = 'NA'
    if include_bams:
        # exclude any samples that do not have BAM data
        num_samples_missing_bams = sequence_results[sequence_results['PATH_y'].isna()].shape[0]
        sequence_results = sequence_results[~sequence_results['PATH_y'].isna()]
    # samples missing consensus or BAM sequence files
    num_samples_missing_bams = sequence_results[sequence_results['PATH_y'].isna()].shape[0]
    num_samples_missing_cons = sequence_results[sequence_results['PATH_x'].isna()].shape[0]
    # ## Make sure to remove any samples that have already been uploaded to github (just an extra safety step)
    # load metadata.csv from github repo, then clean up
    meta_df = pd.read_csv(released_samples_fpath)
    meta_df = meta_df[meta_df['covv_subm_sample_id'].str.contains('SEARCH')]
    # consolidate sample ID format
    meta_df.loc[:, 'sample_id'] = meta_df['covv_subm_sample_id'].apply(process_id)
    # get IDs of samples that have already been released
    released_seqs = meta_df['covv_subm_sample_id'].unique()
    # filter out released samples from all the samples we got
    final_result = sequence_results[~sequence_results['sample_id'].isin(released_seqs)]
    # final_result = sequence_results.copy()
    print(f"Preparing {final_result.shape[0]} samples for release")
    # ## Getting coverage information
    cov_filepaths = bs.get_filepaths(analysis_fpath, data_fmt='tsv', 
                                     data_type='trimmed_bams', 
                                     tech='illumina/reports',
                                     generalised=True,
                                     return_type='list')
    cov_filepaths = [Path(fp) for fp in cov_filepaths]
    # read coverage data and clean it up
    cov_df = pd.concat((pd.read_csv(f, sep='\t').assign(path=f) for f in cov_filepaths))
    cov_df.loc[:,'sample_id'] = cov_df['SAMPLE'].apply(process_coverage_sample_ids)
    cov_df.loc[:,'date'] = cov_df['path'].apply(lambda x: ''.join(x.split('/')[4].split('.')[:3]))
    cov_df = (cov_df.sort_values('date')
              .drop_duplicates(subset=['sample_id'], keep='last'))
    # JOIN results with coverage info
    ans = (
    pd.merge(final_result, cov_df,
             on='sample_id', how='left')
      .assign(
        collection_date = lambda x: pd.to_datetime(x["Collection date"]).dt.strftime("%Y-%m-%d")
    )
      .rename(columns={
        "SEARCH SampleID": "ID",
        "Location": "location",
        "COVERAGE": "percent_coverage_cds",
        "AVG_DEPTH": "avg_depth",
        "Authors": "authors",
        "Originating lab": "originating_lab"
    })
    )
    ans['fasta_hdr'] = ans['Virus name']
    num_samples_missing_coverage = ans[ans['percent_coverage_cds'].isna()].shape[0]
    # compute number of samples below 90% coverage
    low_coverage_samples = ans[ans["percent_coverage_cds"] < min_coverage]
    # ignore samples below minimum coverage and average depth
    qc_filter = (ans["percent_coverage_cds"] >= min_coverage) & (ans["avg_depth"] >= min_depth)
    ans = ans.loc[qc_filter]
    # generate concatenated consensus sequences
    if not dry_run:
        # Transfer files
        transfer_files(ans, out_dir, include_bams=include_bams, ncpus=num_cpus)
        msa_dir = out_dir/'msa'
        if not Path.isdir(msa_dir):
            Path.mkdir(msa_dir);
        seqs_dir = Path(out_dir/'fa')
        copy(ref_path, seqs_dir);
        seqs_fp = bs.concat_fasta(seqs_dir, msa_dir/out_dir.basename());
        # load concatenated sequences
        cns_seqs = SeqIO.parse(msa_dir/out_dir.basename()+'.fa', 'fasta')
        cns_seqs = list(cns_seqs)
        # maps columns of ans to new gisaid format
        with open("../metadata_column_mapping.json", 'r') as infile:
            column_mapping = json.load(infile)['gisaid']
        ans_converted_columns = pd.DataFrame()
        for key in column_mapping:
            ans_converted_columns[key] = ans[column_mapping[key]]
        # GISAID metadata for all samples (out_dir/gisaid_metadata.csv)
        gisaid_meta_df = create_gisaid_meta(ans_converted_columns.copy(), gisaid_meta_cols)
        # generate file containing deletions found
        # generate multiple sequence alignment
        msa_fp = seqs_fp.split('.')[0] + '_aligned.fa'
        if not Path.isfile(Path(msa_fp)):
            msa_fp = bs.align_fasta(seqs_fp, msa_fp, num_cpus=num_cpus);
        # path to new github metadata
        meta_fp = out_dir/'metadata.csv'
        # load multiple sequence alignment
        msa_data = bs.load_fasta(msa_fp, is_aligned=True)
        # identify insertions
        insertions = bm.identify_insertions(msa_data, 
                                         meta_fp=meta_fp, 
                                         patient_zero=patient_zero, 
                                         min_ins_len=1,
                                         data_src='alab')
        # save insertion results to file
        insertions.to_csv(out_dir/'insertions.csv', index=False)
        # identify substitution mutations
        substitutions = bm.identify_replacements(msa_data,
                                    meta_fp=meta_fp,
                                    data_src='alab',
                                    patient_zero=patient_zero)
        # save substitution results to file
        substitutions.to_csv(out_dir/'replacements.csv', index=False)
        # identify deletions
        deletions = bm.identify_deletions(msa_data,
                                        meta_fp=meta_fp,
                                        data_src='alab',
                                        patient_zero=patient_zero,
                                        min_del_len=1)
        # save deletion results to file
        deletions.to_csv(out_dir/'deletions.csv', index=False)
        # identify samples with suspicious INDELs and/or substitutions
        with open('config.json', 'r') as f:
            config = json.load(f)
        nonconcerning_genes = config['nonconcerning_genes']
        nonconcerning_mutations = config['nonconcerning_mutations']
        sus_ids, sus_muts = bm.identify_samples_with_suspicious_mutations(substitutions, 
                                                                          deletions, 
                                                                          insertions,
                                                                          nonconcerning_genes,
                                                                          nonconcerning_mutations)
        sus_muts.to_csv(out_dir/'suspicious_mutations.csv', index=False)
        # collect metadata for white-listed samples
        gisaid_white = gisaid_meta_df[~gisaid_meta_df['covv_virus_name'].isin(sus_ids)]
        # collect metadata for samples that require manual inspection
        gisaid_inspect = gisaid_meta_df[gisaid_meta_df['covv_virus_name'].isin(sus_ids)]
        # save them to files
        gisaid_white.to_csv(out_dir/'clean_gisaid_meta.csv', index=False)
        gisaid_inspect.to_csv(out_dir/'inspect_gisaid_meta.csv', index=False)
        # re-transfer FASTA and BAM files of samples into either white-listed or inspection-listed folders
        retransfer_files(ans.copy(), out_dir, sus_ids, include_bams=include_bams, ncpus=num_cpus)
        bs.separate_alignments(bs.load_fasta(msa_fp, is_aligned=True), sus_ids=sus_ids, 
                                             out_dir=msa_dir, filename=seqs_fp.split('.')[0])
        # generate compressed report containing main results
        bs.generate_release_report(out_dir)
    else:
        sus_ids = []
    if not Path.isdir(out_dir):
        Path.mkdir(out_dir);
    # Data logging
    with open("{}/data_release.log".format(out_dir), 'w') as f:
        f.write(f"Prepared {final_result.shape[0]} samples for release\n")
        f.write(f'{low_coverage_samples.shape[0]} samples were found to have coverage below {min_coverage}%\n')
        f.write(f'{num_samples_missing_coverage} samples are missing coverage information\n')
        f.write(f'{num_samples_missing_cons} samples were ignored because they were missing consensus sequence files\n')
        f.write(f'{num_samples_missing_bams} samples were ignored because they were missing BAM sequence files\n')
        f.write(f"""{len(sus_ids)} samples contain suspicious mutations and require manual inspection. 
        They can be found in {out_dir}/fa_inspect and {out_dir}/bam_inspect\n""")
    print(f"Transfer Complete. All results saved in {out_dir}")