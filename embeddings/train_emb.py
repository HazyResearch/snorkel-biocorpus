#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
------------------------------------------------
Create Word Embeddings
------------------------------------------------

Use Gensim's Word2Vec implementation to create
word (or short phrase) embeddings

'''
import re
import sys
import string
import logging
import argparse
from corpora import TextNormalizer
from gensim.models.phrases import Phrases
from gensim.models.word2vec import LineSentence, Word2Vec

punc_regex       = re.compile("[%s]+" % string.punctuation)
digit_regex      = re.compile("\d")
date_regex       = re.compile("\d{1,2}/\d{1,2}/\d{2,4}")
time_regex       = re.compile("[0-9]+:[0-9]{2,2}(:[0-9]{2,2})*\s*(AM|PM)*")

class TextNormalizer(object):
    
    def __init__(self, corpus, keep_mixedcase=False,
                 keep_digits=False, keep_punctuation=False):
        self.corpus           = corpus
        self.keep_mixedcase   = keep_mixedcase
        self.keep_digits      = keep_digits
        self.keep_punctuation = keep_punctuation
    
    def __iter__(self):
        
        for sentence in self.corpus:
            
            # Mixed Case -> mixed case
            if not self.keep_mixedcase:
                sentence = [token.lower() for token in sentence]
            
            if not self.keep_digits:
                sentence = [digit_regex.sub("0",token).strip() for token in sentence]
            
            if not self.keep_punctuation:
                sentence = [token for token in sentence if punc_regex.sub("",token)]
            
            yield sentence

class PhraseCorpus(object):

    def __init__(self, filename, models, keep_mixedcase=False,
                 keep_digits=False, keep_punctuation=False):

        self.filename         = filename
        self.models           = models
        self.keep_mixedcase   = keep_mixedcase
        self.keep_digits      = keep_digits
        self.keep_punctuation = keep_punctuation

    def __iter__(self):

        # create generator for phrase transformed sentences
        sentences = TextNormalizer(LineSentence(self.filename),
                                   self.keep_mixedcase, self.keep_digits,
                                   self.keep_punctuation)
        for s in sentences:
            if self.models:
                yield phrase_transform(s, self.models, 0)
            else:
                yield s

def load_phrase_models(indir, n):
    """

    :param indir:
    :param n:
    :return:
    """
    models = []
    for _ in range(2, n + 1):
        infile = "%s%sgram.phrase.model" % (indir, n)
        models += [Phrases.load(infile)]
    return models

def phrase_transform(sentence, models, idx):
    """
    Recursively apply Phrase models to sentence
    :param sentence:
    :param models:
    :param idx:
    :return:
    """
    if idx >= len(models):
        return sentence

    m = models[idx]
    return phrase_transform(m[sentence], models, idx + 1)


def main(args):

    models = None if not args.modeldir else load_phrase_models(args.modeldir, args.ngrams)
    corpus = PhraseCorpus(args.infile, models, args.keep_mixedcase, args.keep_digits, args.keep_punc)

    embeddings = Word2Vec(corpus, size=args.dim, sg=int(args.algorithm == "skipgram"),
                          window=args.window, min_count=args.min_count, negative=args.negative,
                          iter=args.iterations, sample=1e-5, workers=args.num_procs)

    embeddings.save("%swords.d%s.w%s.m%s.i%s.bin" % (args.outdir, args.dim,
                                                     args.window, args.min_count, args.iterations))


if __name__ == '__main__':

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--infile", type=str, help="input file")
    parser.add_argument("-o", "--outdir", type=str, help="output directory")
    parser.add_argument("-m", "--modeldir", type=str, default=None,
                        help="trained discounted PMI phrase models")
    parser.add_argument("-p", "--num_procs", type=int, default=1)

    # normalization options
    parser.add_argument("-c", "--keep_mixedcase", action='store_true',
                        help="don't apply lowercase normalization",
                        default=True)
    parser.add_argument("-r", "--keep_digits", action='store_true',
                        help="don't apply digit normalization",
                        default=True)
    parser.add_argument("-b", "--keep_punc", action='store_true',
                        help="don't remove punctuation",
                        default=True)

    parser.add_argument("-s", "--savedict", action='store_true',
                        help="save dictionary to text file",
                        default=True)

    # word2vec paramters
    parser.add_argument("-D", "--dim", type=int, default=50,
                        help="dimension of word embeddings")
    parser.add_argument("-W", "--window", type=int, default=2,
                        help="context window")
    parser.add_argument("-M", "--min_count", type=int, default=25,
                        help="minimum occurrence count")
    parser.add_argument("-N", "--negative", type=int, default=10,
                        help="negative sampling")
    parser.add_argument("-I", "--iterations", type=int, default=1,
                        help="iterations")

    parser.add_argument("-A", "--algorithm", type=str, default="skipgram",
                        help="training algorithm (cbow or skipgram)")
    args = parser.parse_args()

    # argument error, exit
    if not args.infile and not args.outdir:
        parser.print_help()
        sys.exit()

    main(args)
