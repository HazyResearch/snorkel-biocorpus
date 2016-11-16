import os
import sys
from snorkel import SnorkelSession
from pubtator_parsers import PubtatorCorpusParser


if __name__ == '__main__':
    print "Parsing %s to %s..." % (sys.argv[1], sys.argv[2])
    os.environ['SNORKELDB'] = sys.argv[2]

    session = SnorkelSession()

    corpus_parser = PubtatorCorpusParser(sys.argv[1])
    corpus        = corpus_parser.parse_corpus(session, 'PubTator Sample')
    print "Corpus parsed; len = %s." % (len(corpus),)
