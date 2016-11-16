from snorkel.parser import SentenceParser, DocParser
from snorkel.models import Corpus, Sentence, Document, split_stable_id
import re


class PubtatorSentenceParser(SentenceParser):
    """Subs in Pubtator annotations in the NER_tags array"""

    def _scrub(self, mention):
        m = re.sub(r'\'\'', '"', mention)
        m = re.sub(r'`',"'", m)
        return m

    def _check_match(self, mention, toks):
        """Check if a string mention matches a list of tokens, without knowledge of token splits"""
        return re.match(r'[\s\t\-\/\.]*'.join(re.escape(self._scrub(t)) for t in toks), self._scrub(mention)) is not None
    
    def _throw_error(self, sentence_parts, mention, toks, msg="Couldn't find match!"):
        print sentence_parts
        print mention
        print ' '.join(toks)
        raise ValueError(msg)

    def _mark_matched_annotation(self, wi, we, sentence_parts, cid, cid_type):
        for j in range(wi, we):
            if sentence_parts['entity_cids'][j] is None:
                sentence_parts['entity_cids'][j]  = cid
                sentence_parts['entity_types'][j] = cid_type
            
            # Pipe-concatenate multiple labels!
            else:
                sentence_parts['entity_cids'][j]  += "|" + cid
                sentence_parts['entity_types'][j] += "|" + cid_type
    
    def _split_token(self, sentence_parts, abs_offsets, tok_idx, char_idx, mention, toks):
        """
        Split a token, splitting the rest of the CoreNLP parse appropriately as well
        Note that this may not result in a correct pos tag split, and dep tree will no longer be a tree...
        """
        try:
            split_word = sentence_parts['words'][tok_idx]
            split_pt   = char_idx - abs_offsets[tok_idx]
            split_char = split_word[split_pt]
        except IndexError:
            print split_word
            print split_pt
            self._throw_error(sentence_parts, mention, toks)

        # Log non-standard split characters...
        if split_char not in ['-', '_', '/', ',', '.', ':']:
            print "Warning: Non-standard split: mention '%s', split on '%s' in word '%s'" % (mention, split_char, split_word)

        # Split CoreNLP token
        N = len(sentence_parts['words'])
        for k, v in sentence_parts.iteritems():
            if isinstance(v, list) and len(v) == N:
                token = v[tok_idx]

                # If words or lemmas, split the word/lemma
                # Note that we're assuming (anc checking) that lemmatization does not
                # affect the split point
                if k in ['words', 'lemmas']:
                    if token[split_pt].lower() != split_char.lower():
                        raise ValueError("Incorrect split of %s" % split_word)
                    sentence_parts[k][tok_idx] = token[split_pt+1:]
                    sentence_parts[k].insert(tok_idx, token[:split_pt])

                elif k == 'char_offsets':
                    sentence_parts[k][tok_idx] = token + split_pt + 1
                    sentence_parts[k].insert(tok_idx, token)

                # Otherwise, just duplicate the split token's value
                else:
                    sentence_parts[k].insert(tok_idx, token)

    def parse(self, doc, text, annotations):
        
        # Track how many annotations are correctly matches
        matched_annos = []

        # Parse the document, iterating over dictionary-form Sentences
        for sentence_parts in self.corenlp_handler.parse(doc, text):
            _, _, start, end  = split_stable_id(sentence_parts['stable_id'])

            # Try to match with annotations
            # If we don't get a start / end match, AND there is a split character between, we split the
            # token and *modify the CoreNLP parse* here!
            for i, anno in enumerate(annotations):
                _, s, e, mention, cid_type, cid = anno
                si = int(s)
                ei = int(e)

                # Get absolute char offsets, i.e. relative to document start
                # Note: this needs to be re-calculated each time in case we split the sentence!
                abs_offsets = [co + start for co in sentence_parts['char_offsets']]

                # Assume if an annotation starts in one sentence, it also ends in that sentence
                if si >= abs_offsets[0] and si <= abs_offsets[-1]:
                    
                    # Get closest end match; note we assume that the end of the tagged span may be
                    # *shorter* than the end of a token
                    we = 0
                    while we < len(abs_offsets) and abs_offsets[we] < ei:
                        we += 1

                    # Handle cases where we exact match the start token
                    if si in abs_offsets:
                        wi    = abs_offsets.index(si)
                        words = [sentence_parts['words'][j] for j in range(wi, we)]

                        # Full exact match
                        if self._check_match(mention, words):
                            matched_annos.append(i)
                            self._mark_matched_annotation(wi, we, sentence_parts, cid, cid_type)

                        # Truncated ending
                        else:
                            self._split_token(sentence_parts, abs_offsets, we-1, ei, mention, words)

                            # Register and confirm match
                            words = [sentence_parts['words'][j] for j in range(wi, we)]
                            if self._check_match(mention, words):
                                matched_annos.append(i)
                                self._mark_matched_annotation(wi, we, sentence_parts, cid, cid_type)
                            else:
                                self._throw_error(sentence_parts, mention, words)

                    # Handle cases where we don't match the start token
                    else:
                        wi = 0
                        while wi < len(abs_offsets) and abs_offsets[wi+1] < si:
                            wi += 1
                        words = [sentence_parts['words'][j] for j in range(wi, we)]
                        self._split_token(sentence_parts, abs_offsets, wi, si-1, mention, words)

                        # Register and confirm match
                        wi   += 1
                        words = [sentence_parts['words'][j] for j in range(wi, we)]
                        if self._check_match(mention, words):
                            matched_annos.append(i)
                            self._mark_matched_annotation(wi, we, sentence_parts, cid, cid_type)
                        else:
                            self._throw_error(sentence_parts, mention, words)
            yield Sentence(**sentence_parts)

        # Check if we got everything
        if len(annotations) != len(matched_annos):
            print annotations
            print matched_annos
            print "\n"
            for i in set(range(len(annotations))).difference(matched_annos):
                print annotations[i]
            print "\n"
            self._throw_error(sentence_parts, mention, words, msg="Annotations missed!")


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
        doc_id = None
        with open(self.fp, 'rb') as f:
            l = -1
            for line in f:
                l += 1

                # Entries are separated by a blank line
                if len(line.rstrip()) == 0:

                    # Don't save multiple times if multiple blank lines
                    if doc_id is not None:
                        doc = Document(name=doc_id, stable_id=stable_id)
                        corpus.append(doc)
                        for _ in self.sent_parser.parse(doc, text, annos):
                            pass
                        doc_id = None
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
                # Note: some articles do not have abstracts, however they still have this line
                elif l == 1:
                    split = re.split(r'\|', line.rstrip(), maxsplit=2)
                    text += '\n' + split[2]

                # Rest of the lines are annotations
                else:
                    anno = line.rstrip('\n').rstrip('\r').split('\t')
                    if anno[3] == 'NO ABSTRACT':
                        continue
                    else:
                       
                        # Handle cases where no CID is provided...
                        if len(anno) == 5:
                            anno.append("")

                        annos.append(anno)

        session.commit()
        return corpus
