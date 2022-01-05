#!/usr/bin/env bash

cyan="\e[1;36m"
reset="\e[0m"

# update folder content
printf "${cyan}Updating local repo...\n${reset}"
cd /home/al/code/HCoV-19-Genomics
git pull origin master

# move old lineage report to old_lineage_reports
printf  "${cyan}Moving lineage report to old_lineage_reports...\n${reset}"
date=$(git log --graph --pretty=format:%ci lineage_report.csv | head -n 1 | cut -d ' ' -f 2)
mv lineage_report.csv ./old_lineage_reports/${date}_lineage_report.csv

# rename consensus sequences using fasta header to ensure uniformity with metadata.csv
printf  "${cyan}Renaming fasta headers...\n${reset}"
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
pangolin temp

# cleanup
rm temp
rm -r logs
conda deactivate

#sync
# printf "${cyan}Syncing with repo...\n${reset}"
# git add -A
# git commit -m "updated pangolineages"
# git push origin master
