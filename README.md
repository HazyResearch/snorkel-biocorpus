# Snorkel BioCoprus

Initially this is just a pre-processed, Snorkel-format dump of [PubTator](https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/PubTator/);
We will be adding more soon!

## Current contents

*Location: raiders7:/lfs/local/0/ajratner/snorkel-biocorpus/data/*

### Sources
* PubMed abstracts

### Entity Tags
* Genes (via [GNormPlus](http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/GNormPlus/))
* Diseases (via [DNorm](http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/DNorm/))
* Chemicals (via [tmChem](http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/tmChem/))
* Species (via [SR4GN](http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/downloads/SR4GN/))
* Mutations (via [tmVar](http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/pub/tmVar/))


## Running
To download the main PubTator file (10GB compressed; 32GB raw):
```
ftp ftp.ncbi.nlm.nih.gov
> pass
> cd pub/lu/PubTator
> get bioconcepts2pubtator_offsets.gz
> quit

gunzip -k bioconcepts2pubtator_offsets.gz
```

## API Access
To get only specific PubTator annotations, simple API access is supported using PubTator-provided scripts; run:
```
cd pubtator_api
python RESTful.client.post.py -i input/pmids.txt -t tmChem > output/pubtator_data
```
Where `pmids.txt` is a newline-separated list of pubmed IDs, and the `-t` flag accepts `tmChem|tmVar|DNorm|GNormPlus`.
