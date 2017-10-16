"""

"""

import re
import os
import sys
import glob
import codecs
import argparse

article_rgx = re.compile("~~_PMID_([0-9]+)_~~")

def load_line_corpus(filename, sentences=False, encoding="utf-8"):

    corpus = {}
    with codecs.open(filename, "rU", 'utf-8') as fp:

        doc = []
        for line in fp:
            if re.search(article_rgx, line) and not doc:
                doc += [line.strip()]

            elif re.search(article_rgx, line):
                pmid = article_rgx.search(doc[0]).group(1)
                corpus[pmid] = " ".join(doc[1:]) if not sentences else doc[1:]
                doc = [line.strip()]
            else:
                doc += [line.strip()]

        if doc:
            pmid = article_rgx.search(doc[0]).group(1)
            corpus[pmid] = " ".join(doc[1:]) if not sentences else doc[1:]

    return corpus


def align(a, b):

    j = 0
    offsets = []
    for i in range(len(a)):
        if a[i] == ' ':
            continue
        while a[i] != b[j] or b[j] == ' ':
            j+= 1
        offsets.append((i,j))
        j += 1

    return offsets

def main(args):

    if not os.path.exists(args.outputdir):
        os.mkdir(args.outputdir)

    sources = glob.glob("{}/*".format(args.source)) if os.path.isdir(args.source) else [args.source]
    sources = sorted([fp for fp in sources if not os.path.isdir(fp)])

    transformed = glob.glob("{}/*".format(args.transformed)) if os.path.isdir(args.transformed) else [args.transformed]
    transformed = sorted([fp for fp in transformed if not os.path.isdir(fp)])

    if len(transformed) != len(sources):
        print "Error - transformed != sources"
        return

    for fs,ft in zip(sources,transformed):

        source    = load_line_corpus(fs)
        transform = load_line_corpus(ft, sentences=True)

        outpath = ".".join(fs.split(".")[0:-1] + [args.prefix] + fs.split(".")[-1:])
        outpath = "{}/{}".format(args.outputdir, outpath.split("/")[-1])

        with codecs.open(outpath,"w", args.encoding) as fp:
            print outpath

            for pmid in source:

                #
                # 1: Create abs token offsets
                #
                a = source[pmid]
                b = " ".join(transform[pmid])
                offsets = align(a,b)
                rev_offsets = dict([(j, i) for i, j in offsets])

                #
                # 2. Tokenize
                #
                splits = dict.fromkeys([i for i in range(len(b)) if b[i] == ' '])
                t, tokens = [],[]
                for i in range(len(b)):
                    if i in splits:
                        if t:
                            tokens.append(t)
                        t = []
                    else:
                        # sanity check
                        if b[i] != a[rev_offsets[i]]:
                            print "ERROR"
                        t.append((rev_offsets[i],i))
                if t:
                    tokens.append(t)

                abs_char_offset_map = [t[0] for t in tokens]

                #
                # 3. Create sentence breaks
                #
                sbd = [len(s.split()) for s in transform[pmid]]
                tokens = zip(b.split(), abs_char_offset_map)
                sentences = []
                for i,l in enumerate(sbd):
                    words = tokens[0:l]
                    text = transform[pmid][i]
                    tokens = tokens[l:]

                    # sanity check -- do strings match?
                    if not " ".join(zip(*words)[0]) == text:
                        sys.stderr.write("[{}] Alignment ERROR\n".format(pmid))

                    words, abs_offsets = zip(*words)
                    abs_char_offsets =  zip(*abs_offsets)[0]
                    row = [pmid, unicode(i), ",".join(map(unicode, abs_char_offsets)), " ".join(words)]
                    fp.write(u"\t".join(row) + u"\n")


if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-s", "--source", type=str, default=None,  help="original documents")
    argparser.add_argument("-t", "--transformed", type=str, default=None, help="transformed documents")
    argparser.add_argument("-o", "--outputdir", type=str, default=".", help="outout directory")
    argparser.add_argument("-p", "--prefix", type=str, default="processed", help="prefix")
    argparser.add_argument("-e", "--encoding", type=str, default="utf-8", help="encoding")
    args = argparser.parse_args()
    main(args)
