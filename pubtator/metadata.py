import re
import codecs
from snorkel.models import Document, SequenceTag

class MetadataProcessor(object):
    """
    Load external information
    """
    def __init__(self):
        pass


class MetadataProcessor(MetadataProcessor):
    """
    Load external information
    """
    def __init__(self, name="pubtator", encoding="utf-8"):
        self.name = name
        self.encoding = encoding



class PubTatorTagProcessor(MetadataProcessor):
    """
    Load PubTator tags
    """
    def __init__(self, name="PubTator", encoding="utf-8"):

        super(PubTatorTagProcessor, self).__init__(name, encoding)

        self.concept_types = {
            "Gene":            "GNormPlus",
            "Disease":         "DNorm",
            "Chemical":        "tmChem",
            "Species":         "SR4GN",
            "DNAMutation":     "tmVar",
            "ProteinMutation": "tmVar",
            "SNP":             "tmVar"
        }
        self.concept_types = {c_type:self.name + "_" + src for c_type, src in self.concept_types.items()}

    def load_data(self, session, file_path):
        """

        :param session:
        :param file_path:
        :return:
        """
        name2id = dict(session.query(Document.name, Document.id).all())

        tags = []
        for content in self._doc_generator(file_path, self.encoding):
            doc_id, annotations = self._parse(content)
            for anno in annotations:
                doc_id, start, end, mention, concept_type, concept_uid = anno
                src = self.concept_types[concept_type]
                tag = SequenceTag(document_id=name2id[doc_id], abs_char_start=start, abs_char_end=end,
                                  concept_type=concept_type, concept_uid=concept_uid, source=src)
                tags.append(tag)

        session.bulk_save_objects(tags)
        session.commit()
        print("Loaded {} tags...".format(len(tags)))

    def _parse(self, content):
        """

        :param content:
        :return:
        """
        # First line is the title
        split = re.split(r'\|', content[0].rstrip(), maxsplit=2)
        doc_id = int(split[0])

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

        return doc_id, annos

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
            if len(lines) > 0:
                print "**",lines
                yield lines