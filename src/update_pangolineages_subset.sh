#!/usr/bin/env bash

cyan="\e[1;36m"
reset="\e[0m"

# rename consensus sequences using fasta header to ensure uniformity with metadata.csv
printf  "${cyan}Renaming fasta headers...\n${reset}"
cd $1
cd consensus_sequences/
touch ../temp
for i in *.fasta;
do
    awk '/^>/{print ">" substr(FILENAME,1,length(FILENAME)-6); next} 1' ${i} >> ../temp
done

# update Pangolin
printf "${cyan}Updating Pangolin...\n${reset}"
set +u
source /home/al/anaconda3/etc/profile.d/conda.sh
conda activate pangolin
pangolin --update

# run Pangolin
printf "${cyan}Running Pangolin...\n${reset}"
cd ..
pangolin temp -t 25

# cleanup
rm temp
rm -r logs
conda deactivate
