#!/bin/bash

#UCSD_Release_1 
#python3 src/alab_release.py --min-coverage 95 --min-depth 200 --not-dry-run --out-dir /kattegat/2022-07-09b_release --sample-sheet /kattegat/analysis/2022.07.09b/2022-07-02_18-39-50-all.bjorn_summary_MZ_2.csv --cpus 25 --analysis-folder /kattegat/analysis/ --output-metadata /home/al/code/HCoV-19-Genomics/metadata.csv --include-bams

# Alab Release
python3 src/alab_release.py --min-coverage 95 --min-depth 200 --not-dry-run --out-dir /kattegat/2022-07-11_release_pwa_test --cpus 25 --analysis-folder /kattegat/analysis/ --output-metadata /home/al/code/HCoV-19-Genomics/metadata.csv --include-bams
