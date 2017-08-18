import re
import codecs
from snorkel.parser import DocPreprocessor
from snorkel.models import Document, split_stable_id
from snorkel.parser import Parser, ParserConnection, Spacy, Sentence

class PubTatorParser(Parser):
    """
    Parser wrapper for PubTator annotations. Annotations require some
    data munging to map from PubTator to whatever parse is generatered by
    our input parser.

    """

    ENTITY_SEP = '~@~'
    STD_SPLITS_RGX = r'[\s\t\-\/\.]*'

    def __init__(self, parser=Spacy(lang='en'), stop_on_err=True, encoding="utf-8"):
        super(PubTatorParser, self).__init__(name="PubTatorParser", encoding=encoding)
        self.parser = parser
        self.stop_on_err = stop_on_err

    def _scrub(self, mention):
        m = re.sub(r'\'\'|``', '"', mention)
        m = re.sub(r'`', "'", m)
        return m

    def _check_match(self, mention, toks):
        """Check if a string mention matches a list of tokens, without knowledge of token splits"""
        return re.match(PubTatorParser.STD_SPLITS_RGX.join(re.escape(self._scrub(t)) for t in toks) +
                        PubTatorParser.STD_SPLITS_RGX + r'$', self._scrub(mention)) is not None

    def _throw_error(self, sentence_parts, mention, toks, msg="Couldn't find match!"):
        print sentence_parts
        print "Annotation:\t'%s'" % mention
        print "Tagged:\t'%s'" % ' '.join(toks)
        if self.stop_on_err:
            raise ValueError(msg)
        else:
            print 'WARNING:', msg

    def _mark_matched_annotation(self, wi, we, sentence_parts, cid, cid_type):
        for j in range(wi, we):
            if sentence_parts['entity_cids'][j] == 'O':
                sentence_parts['entity_cids'][j] = cid
                sentence_parts['entity_types'][j] = cid_type

            # Pipe-concatenate multiple labels!
            else:
                sentence_parts['entity_cids'][j] += PubTatorParser.ENTITY_SEP + cid
                sentence_parts['entity_types'][j] += PubTatorParser.ENTITY_SEP + cid_type

    def _split_token(self, sentence_parts, abs_offsets, tok_idx, char_idx, mention, toks, left_tok=True):
        """
        Split a token, splitting the rest of the parse appropriately as well
        Note that this may not result in a correct pos tag split, and dep tree will no longer be a tree...
        If target_left=True, then do not include the split character with the left split; vice versa for False
        """
        split_word = sentence_parts['words'][tok_idx]
        split_pt = char_idx - abs_offsets[tok_idx]
        split_char = split_word[split_pt]

        # Decide whether to preserve split or not...
        keep_split = re.match(PubTatorParser.STD_SPLITS_RGX + r'$', split_char) is None
        lsplit_pt = split_pt if not keep_split or left_tok else split_pt + 1
        rsplit_pt = split_pt if keep_split and left_tok else split_pt + 1

        # Split CoreNLP token
        N = len(sentence_parts['words'])
        for k, v in sentence_parts.iteritems():
            if isinstance(v, list) and len(v) == N:
                token = v[tok_idx]

                # If words or lemmas, split the word/lemma
                # Note that we're assuming (anc checking) that lemmatization does not
                # affect the split point
                if k in ['words', 'lemmas']:

                    # Note: don't enforce splitting for lemmas if index is not in range
                    # Essentially, this boils down to assuming that the split will either be correct,
                    # or lemmatization will have chopped the split portion off already
                    if k == 'lemmas' and split_pt > len(token):
                        sentence_parts[k][tok_idx] = ''
                        sentence_parts[k].insert(tok_idx, token)
                    else:
                        sentence_parts[k][tok_idx] = token[rsplit_pt:]
                        sentence_parts[k].insert(tok_idx, token[:lsplit_pt])

                elif k == 'char_offsets':
                    sentence_parts[k][tok_idx] = token + rsplit_pt
                    sentence_parts[k].insert(tok_idx, token)

                # Otherwise, just duplicate the split token's value
                else:
                    sentence_parts[k].insert(tok_idx, token)

    def connect(self):
        return ParserConnection(self)

    def parse(self, doc, text):

        annotations = doc.meta["annotations"]

        # Track how many annotations are correctly matches
        sents = []
        matched_annos = []

        # Parse the document, iterating over dictionary-form Sentences
        for sentence_parts in self.parser.parse(doc, text):
            try:
                _, _, start, end = split_stable_id(sentence_parts['stable_id'])

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
                        if ei > end + 1:
                            print "Skipping cross-sentence mention '%s'" % mention
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
                            while wi < len(abs_offsets) and abs_offsets[wi + 1] < si:
                                wi += 1
                            words = [sentence_parts['words'][j] for j in range(wi, we)]

                            # Split the start token
                            try:
                                self._split_token(sentence_parts, abs_offsets, wi, si - 1, mention, words, left_tok=False)
                            except IndexError:
                                self._throw_error(sentence_parts, mention, words, msg="Token split error")
                                matched_annos.append(i)
                                continue

                            # Adjust abs_offsets, wi and we appropriately
                            abs_offsets = [co + start for co in sentence_parts['char_offsets']]
                            wi += 1
                            we += 1

                        wi = abs_offsets.index(si)
                        words = [sentence_parts['words'][j] for j in range(wi, we)]

                        # Full exact match- mark and continue
                        if self._check_match(mention, words):
                            matched_annos.append(i)
                            self._mark_matched_annotation(wi, we, sentence_parts, cid, cid_type)
                            continue

                        # Truncated ending
                        else:
                            try:
                                self._split_token(sentence_parts, abs_offsets, we - 1, ei, mention, words)
                            except IndexError:
                                self._throw_error(sentence_parts, mention, words, msg="Token split error")
                                matched_annos.append(i)
                                continue

                            # Register and confirm match
                            words = [sentence_parts['words'][j] for j in range(wi, we)]
                            if self._check_match(mention, words):
                                matched_annos.append(i)
                                self._mark_matched_annotation(wi, we, sentence_parts, cid, cid_type)
                            else:
                                self._throw_error(sentence_parts, mention, words)
                                matched_annos.append(i)
                                continue

                yield sentence_parts

                sents.append(sentence_parts)

            except Exception as e:
                print "WARNING: parsing exception {} in document {}".format(e, doc.name)


        # Check if we got everything
        if len(annotations) != len(matched_annos):
            print "Annotations:"
            print annotations
            print "Matched annotations:"
            print matched_annos
            print "\n"
            for i in set(range(len(annotations))).difference(matched_annos):
                print annotations[i]
            print "\n"
            for sent in sents:
                print sent["stable_id"], sent["words"], sent["char_offsets"]
                print "\n"
            if self.stop_on_err:
                raise Exception("Annotations missed!")
            else:
                print "WARNING: Annotations missed!"


class PubTatorDocPreprocessor(DocPreprocessor):
    """
    Load PubTator annotation snapshot

    Entity Tags:

    * Genes     -- GNormPlus  http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/GNormPlus/
    * Diseases  -- DNorm      http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/DNorm/
    * Chemicals -- tmChem     http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/tmChem/
    * Species   -- SR4GN      http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/downloads/SR4GN/
    * Mutations -- tmVar      http://www.ncbi.nlm.nih.gov/CBBresearch/Lu/pub/tmVar/

    Live demo:
    https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/PubTator/

    Latest snapshot available at:
    ftp.ncbi.nlm.nih.gov/pub/lu/PubTator/bioconcepts2pubtator_offsets.gz

    """

    def _pubtator_parser(self, content):
        """

        :param content:
        :return:
        """
        # First line is the title
        split = re.split(r'\|', content[0].rstrip(), maxsplit=2)
        doc_id = int(split[0])
        stable_id = self.get_stable_id(doc_id)

        doc_text = split[2]

        # Second line is the abstract
        # Assume these are newline-separated; is this true?
        # Note: some articles do not have abstracts, however they still have this line
        doc_text += ' ' + re.split(r'\|', content[1].rstrip(), maxsplit=2)[2]

        # Rest of the lines are annotations
        annos = []
        for line in content[2:]:
            anno = line.rstrip('\n').rstrip('\r').split('\t')
            if anno[3] == 'NO ABSTRACT':
                continue
            else:

                # Handle cases where no CID is provided...
                if len(anno) == 5:
                    anno.append("")

                # Handle leading / trailing whitespace
                if anno[3].lstrip() != anno[3]:
                    d = len(anno[3]) - len(anno[3].lstrip())
                    anno[1] = int(anno[1]) + d
                    anno[3] = anno[3].lstrip()

                if anno[3].rstrip() != anno[3]:
                    d = len(anno[3]) - len(anno[3].rstrip())
                    anno[2] = int(anno[2]) - d
                    anno[3] = anno[3].rstrip()
                annos.append(anno)

        # Form a Document
        doc = Document(
            name=doc_id, stable_id=stable_id,
            meta={}
        )

        # Return the doc
        return doc, doc_text, annos

    def _doc_generator(self, file_path, encoding="utf-8"):
        """
        PubTator docs are of the form:

        UID|TITLE|TEXT
        UID|ABSTRACT|TEXT
        UID   SPAN   MENTION   ENTITY_TYPE  MESH_ID
        ...

        See -- data/bioconcepts2pubtator_offsets.sample

        """
        with codecs.open(file_path, "rU", encoding=encoding) as fp:
            lines = []
            for line in fp:
                if len(line.rstrip()) == 0:
                    if len(lines) > 0:
                        yield lines
                        lines = []
                else:
                    lines.append(line)

    def parse_file(self, file_path, file_name):
        """
        Parse abstracts

        :param file_path:
        :param file_name:
        :return:
        """
        for content in self._doc_generator(file_path, self.encoding):
            doc, txt, annos = self._pubtator_parser(content)
            yield doc, txt