#!/bin/bash
set -x

# Specify your API key first.

# Specify your EXEHOME first. EXEHOME=/home/user-name/redefine_prompter
cd ${EXEHOME}


python3 main.py \
        --dataset 'linguistic' \
        --backbone 'chatgpt' \
        --temperature 0.5 \
        --sc_num 5 \
        --output_dir 'output/' \
        --key ${APIKEY} \
        # --start 0 \
        # --end -1 

