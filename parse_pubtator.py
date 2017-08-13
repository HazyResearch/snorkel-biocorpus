"""
Preprocess PubTator snapshot for use with Snorkel v6.2

1) Download snapshot
2) Split snapshot into blocks
3) Parse blocks and load into database

"""
import os
import sys
import glob
import shutil
import argparse
from time import time


def split_pubtator_corpus(file_path, split_size=500000):
    """
    Split PubTator snapshot into blocks of size num_docs
    :return:
    """
    try:
        fp = file_path
        nd = split_size
        ns = None

        # Create directory for the splits
        SPLIT_DIR = "%s.splits_%s/" % (fp, nd)
        if os.path.exists(SPLIT_DIR):
            shutil.rmtree(SPLIT_DIR)
        else:
            os.makedirs(SPLIT_DIR)
        ns_print = ns if ns else ""
        print "Splitting %s into %s splits of %s docs each, saving splits in %s" % (fp, ns_print, nd, SPLIT_DIR)
    except:
        print "USAGE: python split_pubtator_file.py FPATH NDOCS_PER_SPLIT MAX_SPLITS"
        sys.exit(1)

    with open(fp, 'rb') as f:
        s = 0
        d = 0
        f_out = open(SPLIT_DIR + 'split_%s' % s, 'wb')
        for line in f:
            f_out.write(line)
            if len(line.strip()) == 0:
                d += 1
                if d % nd == 0:
                    f_out.close()
                    s += 1
                    if ns is None or s < ns:
                        f_out = open(SPLIT_DIR + 'split_%s' % s, 'wb')
                    else:
                        break
        f_out.close()
        print "Split %s." % d

def main(args):

    session = SnorkelSession()

    # ---------------------------------------
    # 1: Split into blocks
    # ---------------------------------------
    split_pubtator_corpus(args.input_file, split_size=args.split_size)

    # ---------------------------------------
    # 2: Parse documents
    # ---------------------------------------
    filelist = glob.glob("{}.splits_{}/*".format(args.input_file,args.split_size))

    # Iterate through the splits
    start_ts = time()
    for fp in filelist:
        doc_preprocessor = PubTatorDocPreprocessor(fp)
        corpus_parser = CorpusParser(parser=PubTatorParser(stop_on_err=False))
        corpus_parser.apply(doc_preprocessor, parallelism=args.num_procs)
        end_ts = time()
        print "Split completed in [%s]" % (time() - end_ts,)

    print "\nDONE in [%s]" % (time() - start_ts,)


if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-d", "--dbname", type=str, default="postgresql:///biocorpus", help="SNORKELDB enviorn variable")
    argparser.add_argument("-i", "--input_file", type=str, default="data/bioconcepts2pubtator_offsets.sample",
                           help="PubTator snapshot")
    argparser.add_argument("-s", "--split_size", type=int, default=50000, help="Number of documents per split")
    argparser.add_argument("-n", "--num_procs", type=int, default=1, help="Number of processes")
    args = argparser.parse_args()

    os.environ['SNORKELDB'] = args.dbname

    from snorkel import SnorkelSession
    from snorkel.parser import CorpusParser
    from pubtator import PubTatorDocPreprocessor, PubTatorParser

    main(args)

