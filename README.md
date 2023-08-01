# `björn_utils`
This is the code repository for `bjorn_utils` - a suite of miscellaneous tools that can be used to:

* prepare results and data files from SARS-CoV-2 sequencing analysis for release to public databases such as GISAID, Google Cloud, and GitHub

## Installation
* Install Anaconda: [instructions can be found here](https://docs.anaconda.com/anaconda/install/)
* Create the `bjorn` environment
```bash
conda env create -f environment.yml -n bjorn_utils
```
* Activate environment
```bash
conda activate bjorn_utils
```
* Install datafunk (inside the activated environment): [instructions (ensure environment is activated during installation)](https://github.com/cov-ert/datafunk)

## Usage

Current stable branch is "main", use all below instructions on that branch.

### Post-processing of SARS-CoV-2 Sequencing Results for Release to public databases
* Activate `bjorn` environment
```bash
conda activate bjorn_utils
```
* Open `run_alab_release.sh` to specify your parameters such as
    * filepath to sample sheet containing sample metadata (input)
    * filepath to updated metadata of samples that have already been uploaded
    * output directory where results are saved
    * number of CPU cores available for use
    * minimum coverage required for each sample (QC filter)
    * minimum average depth required for each sample (QC filter)
    * sequencing technology used
    * DEFAULT: test parameters
* Open `config.json` to specify your parameters such as
    * list of SARS-CoV-2 genes that are considered non-concerning
        * i.e. the occurrence of open-read frame (ORF) altering mutations can be accepted
        * e.g. ['ORF8', 'ORF10']
    * list of SARS-CoV-2 mutations that are considered non-concerning
        * i.e. the occurrence of `ORF8:Q27_` can be accepted (B117 exists)
        * e.g. ['ORF8:Q27_']
* Run the `run_alab_release.sh` script to initiate the data release pipeline
```bash
bash run_alab_release.sh
```
* `bjorn_utils` assumes the following file structure for the input sequencing data
![Release Structure](figs/alab_release_filestructure.png)
