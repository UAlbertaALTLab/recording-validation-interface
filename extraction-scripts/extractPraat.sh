#!/bin/bash

# Execute Praat script to extract tokens
#praat --run <scriptname> <param1> <param2> ...
# Parameters:
master_directory="/home/ARTSRN/timills/av/backup-mwe/tim-clean/"
word_directory="/home/ARTSRN/timills/av/backup-mwe/tim-clean/Extracted/words/"
sentence_directory="/home/ARTSRN/timills/av/backup-mwe/tim-clean/Extracted/sentences/"
session_codes_file="/home/ARTSRN/timills/av/backup-mwe/tim-clean/speaker-codes.tsv"
word_filename="word_codes.txt"
sentence_filename="sentence_codes.txt"

praat --run extract_sessions.praat "$master_directory" "$word_directory" "$sentence_directory" "$session_codes_file" "$word_filename" "$sentence_filename"

echo "Praat script complete."

