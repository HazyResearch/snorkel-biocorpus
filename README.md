# Snorkel BioCorpus

Initially this is just a pre-processed, Snorkel-format dump of [PubTator](https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/PubTator/). 
We will be adding more soon!

## Database Snapshot

The easiest way to get started is to download a preprocessed Snorkel PostgreSQL database dump. This is a 142 GB file and is ready to use directly with Snorkel. 

To reload, just use `psql snorkel-biocorpus < snorkel_biocorpus.sql`

### Sources
* PubMed abstracts

### Summary Statistics

XXX PubMed Abstracts  
XXX 19XX - 2017

### Entity Tags
* Genes ([GNormPlus](https://www.ncbi.nlm.nih.gov/research/bionlp/Tools/GNormPlus/))
* Diseases ([DNorm](https://www.ncbi.nlm.nih.gov/research/bionlp/Tools/DNorm/))
* Chemicals ([tmChem](https://www.ncbi.nlm.nih.gov/research/bionlp/Tools/tmChem/))
* Species ([SR4GN](https://www.ncbi.nlm.nih.gov/research/bionlp/Tools/sr4gn/))
* Mutations ([tmVar](https://www.ncbi.nlm.nih.gov/research/bionlp/Tools/tmvar/))


## Building the Database


### Full PubTator Snapshot

You can rebuild the entire PubTator database from scratch as follows:

run `install.sh`

This will download the current PubTator snapshot (~10GB compressed; 32GB raw) from `ftp.ncbi.nlm.nih.gov`

Parsing using 16 cores with the [spaCy]() parser takes around XX hours. Parsing with CoreNLP will take longer. 


