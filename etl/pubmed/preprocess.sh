#!/usr/bin/env bash

#
#
#
INPUT=$1
OUTPUT="${INPUT}"
FORMAT="pubtator"

cd extract
python extract_text.py -i ${INPUT} -o ${OUTPUT} -f ${FORMAT}

#
# Tokenize Documents (this uses some external, bio-specific utilities)
#
python tokenize.py -i "${INPUT}/tmp/" -o "${INPUT}/tmp/"

python tokenization_fixes.py -i "${INPUT}/tmp/tokens/" -o "${INPUT}/tmp/"

#
# Create Final Corpus (doc info + 1 sentence per line)
#
python export_line_corpus.py -t "${INPUT}/tmp/fixes/" -s "${INPUT}/tmp/" -o "${OUTPUT}/corpus/"

#
# Extract PubMed Metadata
#

#extract_pubmed_metadata.py