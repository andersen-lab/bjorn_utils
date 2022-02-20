#!/bin/bash

# UCSD Release 
python3 src/alab_release.py --min-coverage 95 --min-depth 200 --not-dry-run --out-dir /asgard/2022-02-17_ucsd_release --sample-sheet /asgard/analysis/2022.02.17_ucsd/2022-02-14_19-36-56-all.bjorn_summary_MZ.csv --cpus 25 --analysis-folder /asgard/analysis/ --output-metadata /home/al/code/HCoV-19-Genomics/metadata.csv --include-bams

# Alab Release
# python3 src/alab_release.py --min-coverage 95 --min-depth 200 --not-dry-run --out-dir /asgard/2022-02-17_release --cpus 25 --analysis-folder /asgard/analysis/ --output-metadata /home/al/code/HCoV-19-Genomics/metadata.csv --include-bams
