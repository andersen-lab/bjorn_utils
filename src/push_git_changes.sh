#!/usr/bin/env bash

cd /home/al/code/HCoV-19-Genomics
git add .
files_added = (git status | wc -l) - 3
git commit -m "Added $files_added sequences from San Diego"
git push 
