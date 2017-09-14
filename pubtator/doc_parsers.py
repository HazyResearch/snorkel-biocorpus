import codecs
from snorkel.parser import DocPreprocessor


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
            if lines:
                yield lines




