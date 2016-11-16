import urllib2
import time
import sys
import getopt

inputfile = ''
bioconcept = ''
format = ''

try:
	options, remainder = getopt.getopt(sys.argv[1:], 'i:b:f:', ['inputfile=','bioconcept=','format='])
except getopt.GetoptError, err:
	print "\npython RESTful.client.get.py -i [inputfile] -b [bioconcept] -f [format]\n"
	print "\t bioconcept: We support five kinds of bioconcepts, i.e., Gene, Disease, Chemical, Species, Mutation. When 'BioConcept' is used, all five are included.\n"
	print "\t inputfile: a file with a pmid list\n"
	print "\t format: PubTator (tab-delimited text file), BioC (xml), and JSON\n\n"
	sys.exit(0)
														 
for opt, arg in options:
	if opt in ('-i', '--inputfile'):
		inputfile = arg
	elif opt in ('-b', '--bioconcept'):
		bioconcept = arg
	elif opt in ('-f', '--format'):
		format = arg

fh = open(inputfile)
for pmid in fh:
	#Submit
	pmid=pmid.rstrip('\r\n')
	url_Submit = "https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/RESTful/tmTool.cgi/" + bioconcept + "/" + pmid + "/" + format + "/"
	urllib_result = urllib2.urlopen(url_Submit)
	print urllib_result.read()
