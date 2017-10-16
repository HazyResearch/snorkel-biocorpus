import re
import sys
import codecs
import lxml.etree as et
from collections import namedtuple
from snorkel.models import Document, SequenceTag


Tag = namedtuple('Tag', 'document_id abs_char_start abs_char_end concept_type concept_uid source')

class MetadataProcessor(object):
    """
    Load external information
    """
    def __init__(self, name, encoding="utf-8"):
        self.name = name
        self.encoding = encoding


class PubMedMetadataProcessor(MetadataProcessor):
    """
    Load external information
    """
    def __init__(self, name="medline_pubmed", encoding="utf-8"):
        """

        :param name:
        :param encoding:
        """
        super(PubMedMetadataProcessor, self).__init__(name, encoding)
        self.mappings = {"issn": {}, "mesh_heading": {}}

    def load_data(self, session, file_path):
        """

        :param session:
        :param file_path:
        :return:
        """
        # target fields for manually extracted data
        doc_xpath           = './/PubmedArticle'
        date_xpath          = './MedlineCitation/DateCompleted'
        id_xpath            = './MedlineCitation/PMID/text()'
        journal_issn_xpath  = "./MedlineCitation/Article/Journal/ISSN/text()"
        journal_title_xpath = "./MedlineCitation/Article/Journal/Title/text()"
        mesh_xpath          = "./MedlineCitation/MeshHeadingList/MeshHeading"

        doc_metadata = {}
        for i, doc in enumerate(et.parse(file_path).xpath(doc_xpath)):
            fields = []
            try:
                pmid = doc.xpath(id_xpath)[0]

                # MEDLINE/PubMed date (later than actual publication?)
                for elem in doc.xpath(date_xpath):
                    ts = [(child.tag, child.text) for child in elem.getchildren()]
                    fields.extend(ts)

                # The ISSN (International Standard Serial Number) identifies resources (e.g., journals)
                issn = doc.xpath(journal_issn_xpath)[0] if doc.xpath(journal_issn_xpath) else None
                title = doc.xpath(journal_title_xpath)[0] if doc.xpath(journal_title_xpath) else None
                if issn:
                    fields.append(('ISSN', issn))
                    self.mappings['issn'][issn] = title

                # Medical Subject Headings
                for elem in doc.xpath(mesh_xpath):
                    for child in elem.getchildren():
                        ui = child.xpath("./@UI")[0]
                        major_topic = child.xpath("@MajorTopicYN")[0]
                        name = "MeshMinor" if major_topic == 'N' else "MeshMajor"
                        fields.append((name, ui))
                        self.mappings['mesh_heading'][ui] = child.xpath("text()")[0]

                # Store the rest as the raw XML
                # TODO

                doc_metadata[pmid] = fields

            except Exception as e:
                print "Error! {}".format(e)
                print et.tostring(doc)
                print "-" * 100

        # build doc_name index
        name2id = dict(session.query(Document.name, Document.id).all())

        # create ContextAttribute
        attributes = []
        for doc_id in doc_metadata:

            if doc_id not in name2id:
                sys.stderr.write("{} not in database, skipping labels...".format(doc_id))
                continue

            for name,value in doc_metadata[pmid]:
                attributes.append(ContextAttribute(document_id=name2id[doc_id], name=name, value=value))

        # commit to database
        try:
            session.bulk_save_objects(attributes)
            session.commit()
            print("Loaded {} tags...".format(len(attributes)))
        except Exception as e:
            print "ERROR! {}".format(e)



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


    def load_data(self, session, file_path, name2id = None):

        # build doc_name index
        if not name2id:
            name2id = dict(session.query(Document.name, Document.id).all())

        tags = set()
        for content in self._doc_generator(file_path, self.encoding):
            doc_name, annotations = self._parse(content)

            if doc_name not in name2id:
                sys.stderr.write("{} not in database, skipping labels...\n".format(doc_name))
                continue

            for anno in annotations:
                doc_name, start, end, mention, concept_type, concept_uid = anno
                src = self.concept_types[concept_type]
                t = Tag(document_id=name2id[doc_name], abs_char_start=start, abs_char_end=end,
                        concept_type=concept_type, concept_uid=concept_uid, source=src)
                tags.add(t)

        return tags


    def commit(self, session, file_path):
        """

        :param session:
        :param file_path:
        :return:
        """
        tags = self.load_data(session, file_path)

        try:
            seq_tags = []
            while tags:
                t = tags.pop()
                seq_tags.append(SequenceTag(**t))
                del t

            session.bulk_save_objects(seq_tags)
            session.commit()
            print("Loaded {} tags...".format(len(seq_tags)))
        except Exception as e:
            print "ERROR! {}".format(e)

    def _parse(self, content):
        """

        :param content:
        :return:
        """
        # First line is the title
        split = re.split(r'\|', content[0].rstrip(), maxsplit=2)
        doc_id = split[0]

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