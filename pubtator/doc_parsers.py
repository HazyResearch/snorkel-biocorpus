import codecs
import spacy
from collections import defaultdict
from snorkel.models import construct_stable_id
from spacy.tokens import Doc
from snorkel.parser import DocPreprocessor
from snorkel.models import Document, split_stable_id
from snorkel.parser import Parser, ParserConnection, Spacy, Sentence

class LineCorpusParser(Parser):
    """
    Slight modification of SpaCy parser to allow whitespace tokenization and manual
    sentence boundary detection (SBD). Due to the clunky way SpaCy deals with SBD,
    we just implement a new class to deal with things.
    """
    def __init__(self, annotators=['tagger', 'parser', 'entity'],
                 lang='en', num_threads=1, tokenize_on_whitespace=True, verbose=False):

        super(LineCorpusParser, self).__init__(name="line_space_corpus")
        self.model = spacy.load(lang, create_make_doc=WhitespaceTokenizer) if tokenize_on_whitespace else \
            spacy.load(lang)
        self.num_threads = num_threads

        self.pipeline = []
        for proc in annotators:
            self.pipeline += [self.model.__dict__[proc]]


    def _original_string(self, tokens, offsets):
        """
        Recreate string with original char offsets
        :param tokens:
        :param offsets:
        :return:
        """
        s = ""
        for t, i in zip(tokens, offsets):
            diff = i - len(s)
            if diff:
                s += ' ' * diff
            s += t
        return s

    def connect(self):
        return ParserConnection(self)

    def parse(self, document, text):
        '''
        Transform spaCy output to match Snorkel's default format
        :param document:
        :param text:
        :return:
        '''
        offsets, sents = zip(*text)
        sents = map(self.to_unicode, list(sents))
        sents = map(Parser.strip_null_bytes, list(sents))

        # parse each individual sentence
        position = 0
        sentences = []
        for abs_char_offsets, text in zip(offsets, sents):

            parts = defaultdict(list)
            doc = self.model.make_doc(text)
            for proc in self.pipeline:
                proc(doc)
            assert doc.is_parsed

            # recreate original text (with correct offsets)
            char_offsets = [i - abs_char_offsets[0] for i in abs_char_offsets]
            text = self._original_string(text.split(), char_offsets)

            for sent in list(doc.sents):
                for i,token in enumerate(sent):
                    parts['words'].append(str(token))
                    parts['lemmas'].append(token.lemma_)
                    parts['pos_tags'].append(token.tag_)
                    parts['ner_tags'].append(token.ent_type_ if token.ent_type_ else 'O')
                    head_idx = 0 if token.head is token else token.head.i - sent[0].i + 1
                    parts['dep_parents'].append(head_idx)
                    parts['dep_labels'].append(token.dep_)

            # Add null entity array (matching null for CoreNLP)
            parts['entity_cids'] = ['O' for _ in parts['words']]
            parts['entity_types'] = ['O' for _ in parts['words']]

            # make char_offsets relative to start of sentence
            parts['char_offsets'] = [
                p - parts['char_offsets'][0] for p in parts['char_offsets']
            ]
            parts['position'] = position

            # Link the sentence to its parent document object
            parts['document'] = document
            parts['text'] = text

            # Add null entity array (matching null for CoreNLP)
            parts['entity_cids'] = ['O' for _ in parts['words']]
            parts['entity_types'] = ['O' for _ in parts['words']]

            parts['char_offsets'] = char_offsets
            parts['abs_char_offsets'] = abs_char_offsets

            # Assign the stable id as document's stable id plus absolute
            # character offset
            abs_sent_offset = abs_char_offsets[0]
            abs_sent_offset_end = abs_sent_offset + char_offsets[-1] + len(parts['words'][-1])
            if document:
                parts['stable_id'] = construct_stable_id(document, 'sentence', abs_sent_offset, abs_sent_offset_end)

            position += 1

            yield parts

class WhitespaceTokenizer(object):
    def __init__(self, nlp):
        self.vocab = nlp.vocab

    def __call__(self, text):
        words = text.split(' ')
        spaces = [True] * len(words)
        return Doc(self.vocab, words=words, spaces=spaces)

class PretokenizedDocPreprocessor(DocPreprocessor):
    """
    Assumes text has already been preprocessed for:
     - Sentence Boundary Detection (SBD)
     - Word tokenization

    Format:
    DOCUMENT_ID     SENTENCE

    """

    def _doc_generator(self, file_path, encoding="utf-8"):
        """

        """
        with codecs.open(file_path, "rU", encoding=encoding) as fp:
            curr = None
            lines = []
            for line in fp:

                s = line.strip().split("\t")
                doc_name = s[0]
                s[1] = int(s[1])
                s[2] = map(int, s[2].split(","))

                if curr == doc_name or curr == None:
                    lines.append(s)
                    curr = doc_name
                elif curr != doc_name:
                    yield lines
                    curr = doc_name
                    lines = [s]

            if lines:
                yield lines


    def _line_corpus_parser(self, content):
        """
        :param content:
        :return:
        """

        doc_name = None
        sents = []
        for line in content:
            doc_name = line[0]
            sents.append(line[2:])

        stable_id = self.get_stable_id(doc_name)

        # Form a Document
        doc = Document(
            name=doc_name, stable_id=stable_id,
            meta={}
        )

        # Return the doc
        return doc, sents

    def parse_file(self, file_path, file_name):
        """
        Parse abstracts

        :param file_path:
        :param file_name:
        :return:
        """
        for content in self._doc_generator(file_path, self.encoding):
            doc, txt = self._line_corpus_parser(content)
            yield doc, txt

