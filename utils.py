from snorkel.parser import SentenceParser, DocParser
from snorkel.models import Corpus, Sentence, Document, split_stable_id
import re


class PubtatorSentenceParser(SentenceParser):
    """Subs in Pubtator annotations in the NER_tags array"""
    def parse(self, doc, text, annotations):
        for parts in self.corenlp_handler.parse(doc, text):

            # Get absolute char offsets, i.e. relative to document start
            _, _, start, end  = split_stable_id(doc.stable_id)
            abs_char_offsets = [co + start for co in parts['char_offsets']]

            # Try to match with annotations
            for _, s, e, mention, cid_type, cid in annotations:
                
                # Tag format: e.g. "Disease:MESH:D000013"
                tag = "%s:%s" % (cid_type, cid)

                # Sub in for the ner_tag
                wi  = abs_char_offsets.index(int(s))
                while wi < len(abs_char_offsets) and abs_char_offsets[we] <= int(e):
                    parts['ner_tags'][wi] = tag
            yield Sentence(**parts)


class PubtatorCorpusParser(object):
    """
    See: https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/PubTator/tutorial/index.html#ExportannotationinPubTator
    """
    def __init__(self, fp):
        self.fp          = fp
        self.sent_parser = PubtatorSentenceParser()
        
    def parse_corpus(self, session, name):
        
        # Create new Corpus
        corpus = Corpus(name=name)
        session.add(corpus)

        # Parse the Pubtator file
        with open(self.fp, 'rb') as f:
            l = -1
            for line in f:
                l += 1

                # Entries are separated by a blank line
                if len(line.rstrip('\n')) == 0:
                    doc = Document(name=doc_id, stable_id=stable_id)
                    corpus.append(doc)
                    for _ in self.sent_parser.parse(doc, text, annos):
                        pass
                    l = -1
                    continue

                # First line is the title
                if l == 0:
                    split     = re.split(r'\|', line.rstrip(), maxsplit=2)
                    doc_id    = int(split[0])
                    stable_id = "%s::document:0:0" % doc_id
                    text      = split[2]
                    annos     = []

                # Second line is the abstract
                # Assume these are newline-separated; is this true?
                elif l == 1:
                    split = re.split(r'\|', line.rstrip(), maxsplit=2)
                    text += '\n' + split[2]

                # Rest of the lines are annotations
                else:
                    annos.append(line.split('\t'))

        doc = Document(name=doc_id, stable_id=stable_id)
        corpus.append(doc)
        for _ in self.sent_parser.parse(doc, text, annos):
            pass

        session.commit()
        return corpus
