'''
Dumps PubMed standoff abstracts to a common text file format for bulk loading

'''

import os
import glob
import codecs
import argparse
import lxml.etree as et
from pubtator.parsers import PubTatorDocPreprocessor


def parse_standoff_format(filename, outputdir, source_prefix="gold_cdr"):
    """

    FORMAT:
        DOC_ID  CHAR_STAR    CHAR_END   CONCEPT_TYPE CONCEPT_ID SOURCE
        100000	1060	1065	Chemical	CHEBI:53351	PubTator_tmChem

    :param filename:
    :param outputdir:
    :return:
    """
    pubtator = PubTatorDocPreprocessor("", annotations=True)

    errors = 0
    outfile = os.path.basename(filename)
    outfile = ".".join(outfile.split(".")[0:-1])
    outfile = "{}/{}.tags.txt".format(outputdir.replace(os.path.basename(filename), ""), outfile)

    with codecs.open(outfile, "w", "utf-8") as op:
        for doc, text, annos in pubtator.parse_file(filename, filename):
            for a in annos:
                if len(a) == 4:
                    continue

                a = a[0:6]
                try:
                    pmid, start, end, text, ctype, cid = a
                    row = [pmid, start, end, ctype, cid]
                    op.write("\t".join(row + [source_prefix]) + u"\n")

                except Exception as e:
                    print e

    print "Wrote", outfile
    return errors


def main(args):

    doc_parser = parse_standoff_format

    filelist = glob.glob("{}/*".format(args.inputdir)) if os.path.isdir(args.inputdir) else [args.inputdir]
    filelist = [fp for fp in filelist if not os.path.isdir(fp)]

    for fp in filelist:
        if not os.path.exists(args.outputdir):
            os.mkdir(args.outputdir)

        errors = doc_parser(fp, args.outputdir)
        if errors:
            print "Errors: {}".format(errors)


if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-i", "--inputdir", type=str, default="input directory or file")
    argparser.add_argument("-o", "--outputdir", type=str, default="outout directory")

    args = argparser.parse_args()


    main(args)
