#!/usr/bin/env bash

# configure this for your specific machine
NUM_PROCS=16

INIT_DB=false
DB_HOST="localhost"
DB_NAME="biocorpus"
DB_PORT=4554

#
# Download Snorkel
#
if [ ! -d "snorkel" ]; then
   echo "Downloading Snorkel..."
   git clone https://github.com/HazyResearch/snorkel.git
   cd snorkel
   git submodule update --init --recursive
   cd ..
fi

#
# Check if PubTator data is downloaded
#
if [ ! -e "data/bioconcepts2pubtator_offsets" ]; then
   echo "Downloading PubTator data snapshot..."
   wget ftp://anonymous:@ftp.ncbi.nlm.nih.gov/pub/lu/PubTator/bioconcepts2pubtator_offsets.gz

   gunzip -k bioconcepts2pubtator_offsets.gz
   rm bioconcepts2pubtator_offsets.gz

   if [ ! -d "data" ]; then
      mkdir data
   fi
   mv bioconcepts2pubtator_offsets data/.
   echo "Downloading complete"
fi

#
# Initalize psql database
#
DB_CONN="${DB_HOST}:${DB_PORT}/${DB_NAME}"

if ["$INIT_DB" = true]; then
   SQL="DROP DATABASE IF EXISTS ""${DB_NAME}"";"
   psql -h "${DB_HOST}" -p "${DB_PORT}" -d postgres -c "${SQL}"

   sql="CREATE DATABASE ""${DB_NAME}"";"
   psql -h "${DB_HOST}" -p "${DB_PORT}" -d postgres -c "${SQL}"
fi

#
# ETL script: split dataset into blocks, parse, then load into database
#
echp "Generating PostgreSQL database: ${DB_CONN}"
source set_env.sh python parse_pubtator.py --input_file data/bioconcepts2pubtator_offsets --dbname "${DB_CONN}" -n "${NUM_PROCS}" > biocorpus.log 2> biocorpus.err
