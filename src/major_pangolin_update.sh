#!/usr/bin/env bash
# Use this file to update pangolin between major release changes
cyan="\e[1;36m"
reset="\e[0m"

printf "${cyan}Entering pangolin repository and fetching updates via git...\n${reset}"
cd /home/al/code/pangolin
git pull

printf "${cyan}Activating and updating conda environement...\n${reset}"
conda env update -f environment.yml
pip install .
