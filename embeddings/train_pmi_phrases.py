#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
------------------------------------------------
Learn Common Phrases
------------------------------------------------

Train PMI-based phrase models. Currently this only assumes bigrams,
but it can be extended easily.

"""
import sys
import logging
import argparse
from utils import exec_time
from corpora import TextNormalizer
from gensim.models.phrases import Phrases
from gensim.models.word2vec import LineSentence


def main(args):
    sentences = TextNormalizer(LineSentence(args.infile), 
                               args.keep_mixedcase, args.keep_digits, args.keep_punc)

    # build initial bigram phrase model
    model = Phrases(sentences, min_count=5, threshold=10)
    model.save("%sphrase.model" % (args.outdir))

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--infile", type=str, help="input sentence corpus")
    parser.add_argument("-o","--outdir", type=str,  help="output directory for phrase models")

    parser.add_argument("-c","--keep_mixedcase", action='store_true',
                        help="don't apply lowercase normalization",
                        default=True)
    parser.add_argument("-r","--keep_digits", action='store_true', 
                        help="don't apply digit normalization",
                        default=True)
    parser.add_argument("-b","--keep_punc", action='store_true', 
                        help="don't remove punctuation",
                        default=True)
     
    args = parser.parse_args()

    # argument error, exit
    if not args.infile:
        parser.print_help()
        sys.exit()

    main(args)
    