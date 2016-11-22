from snorkel.parser import SentenceParser, DocParser
from snorkel.models import Corpus, Sentence, Document, split_stable_id
from snorkel.udf import UDF
import re


ENTITY_SEP     = '~@~'
STD_SPLITS_RGX = r'[\s\t\-\/\.]*'

class PubtatorSentenceParser(SentenceParser):
    """Subs in Pubtator annotations in the NER_tags array"""

    def _scrub(self, mention):
        m = re.sub(r'\'\'|``', '"', mention)
        m = re.sub(r'`',"'", m)
        return m

    def _check_match(self, mention, toks):
        """Check if a string mention matches a list of tokens, without knowledge of token splits"""
        return re.match(STD_SPLITS_RGX.join(re.escape(self._scrub(t)) for t in toks) + STD_SPLITS_RGX + r'$', self._scrub(mention)) is not None
    
    def _throw_error(self, sentence_parts, mention, toks, msg="Couldn't find match!"):
        print "\n"
        print sentence_parts
        print "Annotation: '%s'" % mention
        print "Tagged: '%s'" % ' '.join(toks)
        raise ValueError(msg)

    def _mark_matched_annotation(self, wi, we, sentence_parts, cid, cid_type):
        for j in range(wi, we):
            if sentence_parts['entity_cids'][j] == 'O':
                sentence_parts['entity_cids'][j]  = cid
                sentence_parts['entity_types'][j] = cid_type
            
            # Pipe-concatenate multiple labels!
            else:
                sentence_parts['entity_cids'][j]  += ENTITY_SEP + cid
                sentence_parts['entity_types'][j] += ENTITY_SEP + cid_type
    
    def _split_token(self, sentence_parts, abs_offsets, tok_idx, char_idx, mention, toks, left_tok=True):
        """
        Split a token, splitting the rest of the CoreNLP parse appropriately as well
        Note that this may not result in a correct pos tag split, and dep tree will no longer be a tree...
        If target_left=True, then do not include the split character with the left split; vice versa for False
        """
        try:
            split_word = sentence_parts['words'][tok_idx]
            split_pt   = char_idx - abs_offsets[tok_idx]
            split_char = split_word[split_pt]
        except IndexError:
            print "\r"
            print split_word
            print split_pt
            self._throw_error(sentence_parts, mention, toks)

        # Decide whether to preserve split or not...
        keep_split = re.match(STD_SPLITS_RGX + r'$', split_char) is None
        lsplit_pt  = split_pt if not keep_split or left_tok else split_pt + 1
        rsplit_pt  = split_pt if keep_split and left_tok else split_pt + 1

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
                    sentence_parts[k][tok_idx] = token[rsplit_pt:]
                    sentence_parts[k].insert(tok_idx, token[:lsplit_pt])

                elif k == 'char_offsets':
                    sentence_parts[k][tok_idx] = token + rsplit_pt
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

                # Consider annotations that are in this sentence
                if si >= start and si < end:

                    # We assume mentions are contained within a single sentence, otherwise we skip
                    # NOTE: This is the one type of annotation we do *not* include!
                    if ei > end:
                        print "\rSkipping cross-sentence mention %s\n" % mention
                        matched_annos.append(i)
                        continue
                    
                    # Get absolute char offsets, i.e. relative to document start
                    # Note: this needs to be re-calculated each time in case we split the sentence!
                    abs_offsets = [co + start for co in sentence_parts['char_offsets']]

                    # Get closest end match; note we assume that the end of the tagged span may be
                    # *shorter* than the end of a token
                    we = 0
                    while we < len(abs_offsets) and abs_offsets[we] < ei:
                        we += 1

                    # Handle cases where we *do not* match the start token first by splitting start token
                    if si not in abs_offsets:
                        wi = 0
                        while wi < len(abs_offsets) and abs_offsets[wi+1] < si:
                            wi += 1
                        words = [sentence_parts['words'][j] for j in range(wi, we)]

                        # Split the start token
                        self._split_token(sentence_parts, abs_offsets, wi, si-1, mention, words, left_tok=False)

                        # Adjust abs_offsets, wi and we appropriately
                        abs_offsets = [co + start for co in sentence_parts['char_offsets']]
                        wi         += 1
                        we         += 1

                    wi    = abs_offsets.index(si)
                    words = [sentence_parts['words'][j] for j in range(wi, we)]

                    # Full exact match- mark and continue
                    if self._check_match(mention, words):
                        matched_annos.append(i)
                        self._mark_matched_annotation(wi, we, sentence_parts, cid, cid_type)
                        continue

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

            yield Sentence(**sentence_parts)

        # Check if we got everything
        if len(annotations) != len(matched_annos):
            print annotations
            print matched_annos
            print "\n"
            for i in set(range(len(annotations))).difference(matched_annos):
                print annotations[i]
            raise Exception("Annotations missed!")


class PubtatorDocParser(UDF):
    def __init__(self, x_queue=None, y_queue=None):
        UDF.__init__(self, x_queue, y_queue)
        self.sent_parser = PubtatorSentenceParser(disable_ptb=True)

    def apply(self, lines):
        
        # Here, lines are the lines of a PubTator-format file corresponding to on one document
        # + its annotations

        # First line is the title
        split     = re.split(r'\|', lines[0].rstrip(), maxsplit=2)
        doc_id    = int(split[0])
        stable_id = "%s::document:0:0" % doc_id
        text      = split[2]

        # Second line is the abstract
        # Assume these are newline-separated; is this true?
        # Note: some articles do not have abstracts, however they still have this line
        text += '\n' + re.split(r'\|', lines[1].rstrip(), maxsplit=2)[2]

        # Rest of the lines are annotations
        annos = []
        for line in lines[2:]:
            anno = line.rstrip('\n').rstrip('\r').split('\t')
            if anno[3] == 'NO ABSTRACT':
                continue

            # Handle cases where no CID is provided...
            else:
                if len(anno) == 5:
                    anno.append("")
                annos.append(anno)

        # Form a Document
        doc = Document(name=doc_id, stable_id=stable_id)

        # Parse the sentences
        for _ in self.sent_parser.parse(doc, text, annos):
            pass

        # Return the doc
        yield doc


def pubtator_doc_generator(fp):
    with open(fp, 'rb') as f: 
        lines = []
        for line in f:
            if len(line.rstrip()) == 0:
                if len(lines) > 0:
                    yield lines
                    lines = []
            else:
                lines.append(line)
