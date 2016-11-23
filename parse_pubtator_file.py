import os
import sys
from time import time


if __name__ == '__main__':
    print "Parsing splits in %s to %s, parallelism=%s" % (sys.argv[1], sys.argv[2], int(sys.argv[3]))
    ROOT = sys.argv[1]

    # Initialize Snorkel session
    os.environ['SNORKELDB'] = sys.argv[2]

    # Import statements for snorkel go here...
    from snorkel import SnorkelSession
    from pubtator_parsers import PubtatorDocParser, pubtator_doc_generator
    from snorkel.udf import UDFRunnerMP

    # Start snorkel session
    session = SnorkelSession()

    # Iterate through the splits
    t0 = time()
    for fp_rel in os.listdir(sys.argv[1]):
        fp = ROOT + fp_rel
        print "Parsing %s..." % fp
        t1            = time()
        doc_generator = pubtator_doc_generator(fp)
        corpus_parser = UDFRunnerMP(PubtatorDocParser)
        corpus_parser.run(doc_generator, parallelism=int(sys.argv[3]))
        session.commit()
        print "Done in %s." % (time() - t1,)
    
    print "\nDONE in %s." % (time() - t0,)
