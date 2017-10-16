"""
Generate external database key/value pairs for select fields that
we want to define joins or elastic search attributes over
(e.g., publication year, journal, mesh keywords). The rest of the
content we commit as a the raw XML tree.
"""

import glob
import lxml.etree as et


filelist = glob.glob("{}/*.xml".format())

fp = inputdir

# target fields for manually extracted data
doc_xpath           = './/PubmedArticle'
date_xpath          = './MedlineCitation/DateCompleted'
id_xpath            = './MedlineCitation/PMID/text()'
journal_issn_xpath  = "./MedlineCitation/Article/Journal/ISSN/text()"
journal_title_xpath = "./MedlineCitation/Article/Journal/Title/text()"
mesh_xpath          = "./MedlineCitation/MeshHeadingList/MeshHeading"

mappings = {"issn":{},"mesh_heading":{}}
doc_metadata = {}
for i, doc in enumerate(et.parse(fp).xpath(doc_xpath)):
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
            fields.append(('ISSN',issn))
            mappings['issn'][issn] = title

        # Medical Subject Headings
        for elem in doc.xpath(mesh_xpath):
            for child in elem.getchildren():
                ui = child.xpath("./@UI")[0]
                major_topic = child.xpath("@MajorTopicYN")[0]
                name = "MeshMinor" if major_topic =='N' else "MeshMajor"
                fields.append((name,ui))
                mappings['mesh_heading'][ui] = child.xpath("text()")[0]

        # Store the rest as the raw XML
        # TODO

        doc_metadata[pmid] = fields

    except Exception as e:
        print "Error! {}".format(e)
        print et.tostring(doc)
        print "-" * 100

for pmid in doc_metadata:
    for field,value in doc_metadata[pmid]:
        row = [pmid, field, value]
        print "\t".join(row)

for category in mappings:
    for name in mappings[category]:
        row = [category, name, mappings[category][name]]
        print "\t".join(row)
