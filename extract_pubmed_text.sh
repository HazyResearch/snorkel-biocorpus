#!/usr/bin/env bash

#
# Create PubMed Sentence Corpus
#
# 1) Extract titles and article text from MEDLINE/PubMed XML docs
# 2) Perform Sentence Boundary Detection (SBD) using GENIA sentence splitter
#     -- http://www.nactem.ac.uk/y-matsu/geniass/
# 3) Tokenize sentences using a chemical-entity aware rule-based tokenizer ChemTok-1.0.1
#    --
#
# NOTE: Any SBD and tokenizer will work here. The key
#

# Simple regex for pulling out abstract text
# run in pubmed directory
egrep -oh "(<ArticleTitle>|<AbstractText>)(.*)(</ArticleTitle>|</AbstractText>)" *.xml | sed 's/<ArticleTitle>//g' | sed 's/<AbstractText>//g' | sed 's/<\/AbstractText>//g' | sed 's/<\/ArticleTitle>//g' > medline_pubmed.raw.txt


# sentence boundary detection
./geniass ~/data/lscratch/medline_pubmed.raw.txt ~/data/lscratch/medline_pubmed.sentences.txt

# tokenization
java -jar chemtok-1.0.1.jar < ~/data/lscratch/medline_pubmed.sentences.txt > ~/data/lscratch/medline_pubmed.tokens.txt