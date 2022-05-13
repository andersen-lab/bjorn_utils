#!/usr/bin/env bash

cd /home/al/code/HCoV-19-Genomics
git add .
git commit -m "Added $(git status | grep "\.fasta$" | wc -l) sequences from San Diego"
git push 
