#!/usr/bin/env bash

#
# The NLM provides a MEDLINE/PubMed abstract baseline dataset that is updated every December.
#
# See:
#
wget -r --no-parent -r -nH -nd -np ftp://anonymous:@ftp.ncbi.nlm.nih.gov/pubmed/baseline


#
# PMC Open Access Subset
# + PLOS
# + BioMed Central
#
# See: https://www.ncbi.nlm.nih.gov/pmc/tools/ftp/
# http://api.plos.org/text-and-data-mining/

wget -r --no-parent -r -nH -nd -np ftp://anonymous:@ftp.ncbi.nlm.nih.gov/pub/pmc/oa_bulk
