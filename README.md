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


## Rerunning
To download the main PubTator file (10GB compressed; 32GB raw):
```
ftp ftp.ncbi.nlm.nih.gov
> pass
> cd pub/lu/PubTator
> get bioconcepts2pubtator_offsets.gz
> quit

gunzip -k bioconcepts2pubtator_offsets.gz
rm bioconcepts2pubtator_offsets.gz
mkdir data
mv bioconcepts2pubtator_offsets data/.
```

Next, we split this file into several chunks for convenience:
```
python split_pubtator_file.py data/bioconcepts2pubtator_offsets N_DOCS_PER_SPLIT [MAX_SPLITS]
```
where we used `N_DOCS_PER_SPLIT=500000`.

Finally, run the parsing in parallel:
```
python parse_pubtator_file.py data/bioconcepts2pubtator_offsets.splits_500000/ postgres:///snorkel-biocorpus PARALLELISM 1> log1.txt 2> log2.txt
```

## API Access
To get annotations for specific PubMed abstracts, by PMID, simple API access is supported by the NCBI (see [here](https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/tmTools/#RESTfulIntroduction)):
```
cd pubtator_api
python RESTful.client.get.py -i input/pmids.txt -b BioConcept -f PubTator > output/pubtator_data
```
Where `pmids.txt` is a newline-separated list of pubmed IDs and `pubtator_data` is the destination output file.

_Note: this also supports POST API requests for processing of provided text data; but there are probably limits on abusing this..._
