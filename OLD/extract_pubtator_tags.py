"""
Load PubTator snapshot for use with Snorkel v6.2
This loads tags into memory, so it works best when the input PubTator
file is split into smaller blocks.

"""
import os
import glob
import codecs
import argparse

def dump2delimited(tags, outfile, write_mode, sep=u"\t", encoding="utf-8"):

    with codecs.open(outfile, write_mode, encoding) as fp:
        for t in tags:
            row = [t.document_id, t.abs_char_start, t.abs_char_end,
                   t.concept_type, t.concept_uid, t.source]
            row = map(unicode, row)
            fp.write(sep.join(row) + u"\n")


def main(args):

    session = SnorkelSession()

    # ---------------------------------------
    # 1: Load documents
    # ---------------------------------------
    filelist = glob.glob("{}/*".format(args.input_file))

    write_mode = "w"
    pubtator_tags = PubTatorTagProcessor()
    name2id = dict(session.query(Document.name, Document.id).all())

    for fp in filelist:
        # dump all tags to a tab-delimited text file
        if args.dump:
            tags = pubtator_tags.load_data(session, fp, name2id)
            dump2delimited(tags, args.output_file, write_mode)
            # change to append mode after first write
            write_mode = "a"
        # or commit tags directly to the database
        else:
            pubtator_tags.commit(session, fp)
        print "Loaded tags from {}".format(os.path.basename(fp))

    tags = session.query(SequenceTag.id).all()
    print "Loaded {} PubTator tags".format(len(tags))

if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-d", "--dbname", type=str, default="postgresql:///biocorpus",
                           help="SNORKELDB enviorn variable")
    argparser.add_argument("-i", "--input_file", type=str, default="data/bioconcepts2pubtator_offsets.sample",
                           help="PubTator snapshot")
    argparser.add_argument("-o", "--output_file", type=str, default="tag_dump.tsv",
                           help="PubTator dump filename")
    argparser.add_argument("-D", "--dump", action="store_true", help="Dump PubTator tags to TSV")

    args = argparser.parse_args()

    print args
    os.environ['SNORKELDB'] = args.dbname
    os.environ['TIKA_LOG_PATH'] = "."

    from snorkel import SnorkelSession
    from snorkel.models import SequenceTag, Document
    from pubtator import PubTatorTagProcessor

    main(args)

