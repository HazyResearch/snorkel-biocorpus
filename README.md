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
* Genes (via [GNormPlus](http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/GNormPlus/))
* Diseases (via [DNorm](http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/DNorm/))
* Chemicals (via [tmChem](http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/tmChem/))
* Species (via [SR4GN](http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/downloads/SR4GN/))
* Mutations (via [tmVar](http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/pub/tmVar/))


## Rebuilding the Database
You can rebuild the entire PubTator database from scratch as follows:

run `install.sh`

This will download the current PubTator snapshot (~10GB compressed; 32GB raw) from `ftp.ncbi.nlm.nih.gov`

Parsing using 16 cores with the [spaCy]() parser takes around XX hours. Parsing with CoreNLP will take longer. 


## API Access
To get annotations for specific PubMed abstracts, by PMID, simple API access is supported by the NCBI (see [here](https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/tmTools/#RESTfulIntroduction)):
```
cd pubtator_api
python RESTful.client.get.py -i input/pmids.txt -b BioConcept -f PubTator > output/pubtator_data
```
Where `pmids.txt` is a newline-separated list of pubmed IDs and `pubtator_data` is the destination output file.

_Note: this also supports POST API requests for processing of provided text data; but there are probably limits on abusing this..._
