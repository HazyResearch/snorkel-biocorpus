import re
import sys
from itertools import product
from sqlalchemy.sql import select
from collections import defaultdict
from snorkel.udf import UDF, UDFRunner
from snorkel.models import TemporarySpan, Sentence, Document, SequenceTag, Candidate


class SequenceTagCandidateExtractor(UDFRunner):
    """UDFRunner for SequenceTagCandidateExtractorUDF"""
    def __init__(self, candidate_class, entity_types, tag_sources=['.*'], self_relations=False, 
                 nested_relations=False, symmetric_relations=True):
        super(SequenceTagCandidateExtractor, self).__init__(
            SequenceTagCandidateExtractorUDF, candidate_class=candidate_class,
            entity_types=entity_types, tag_sources=tag_sources, self_relations=self_relations,
            nested_relations=nested_relations, symmetric_relations=symmetric_relations,
        )

    def apply(self, xs, split=0, **kwargs):
        super(SequenceTagCandidateExtractor, self).apply(xs, split=split, **kwargs)

    def clear(self, session, split, **kwargs):
        session.query(Candidate).filter(Candidate.split == split).delete()

class SequenceTagCandidateExtractorUDF(UDF):
    """
    An extractor for pre-tagged entities, stored as SequenceTag objects
    """
    def __init__(self, candidate_class, entity_types, tag_sources=['.*'], self_relations=False, 
                 nested_relations=False, symmetric_relations=False, **kwargs):
        self.candidate_class     = candidate_class
        self.entity_types        = entity_types
        self.tag_sources         = [re.compile(p) for p in tag_sources]
        self.arity               = len(entity_types)
        self.self_relations      = self_relations
        self.nested_relations    = nested_relations
        self.symmetric_relations = symmetric_relations
        self.cache = {}
        super(SequenceTagCandidateExtractorUDF, self).__init__(**kwargs)
        
        
    def _map_annotations(self, doc, tags):
        """
        Take sequence tags, defined by absolute char offsets, and map to sentence/span objects
        :param:
        :param:
        :return tuple of sentence index and tag, (int, SequenceTag)
        """
        spans = []
        char_index = [s.abs_char_offsets[0] for s in doc.sentences]

        for t in tags:
            position = None
            for i in range(len(char_index) - 1):
                if t.abs_char_start >= char_index[i] and t.abs_char_end <= char_index[i+1]:
                    position = i
                    break
            if position == None and t.abs_char_start >= char_index[-1]:
                position = len(char_index) - 1
            if position == None:
                sys.stderr.write("Warning! Cross-sentence mention (skipping...)\n")
                continue
            try:
                shift = doc.sentences[position].abs_char_offsets[0]
                span = doc.sentences[position].text[t.abs_char_start-shift:t.abs_char_end-shift]
                spans.append((position, t))
            except Exception as e:
                print "Error!",e

        return spans
    
    def apply(self, context, clear, split, check_for_existing=True, **kwargs):
        """Extract Candidates from a Context"""
        # For now, just handle Sentences
        if not isinstance(context, Sentence):
            raise NotImplementedError("%s is currently only implemented for Sentence contexts." % self.__name__)
       
        # Load and remap this entire parent document's tag set
        if context.document.id not in self.cache:
            tags = self.session.query(SequenceTag).filter(SequenceTag.document_id==context.document.id).all()
            # filter to 1) target concept/entity types and 2) target sources (e.g., PutTator, TaggerOne)
            tags = [t for t in tags if t.concept_type in set(self.entity_types)]
            tags = [t for t in tags if len([rgx.search(t.source) for rgx in self.tag_sources]) > 0]
            
            tags = self._map_annotations(context.document, tags)
            self.cache[context.document.id] = defaultdict(list)
            for position, tag in tags:
                self.cache[context.document.id][position].append(tag)
        
        # no tags for this Sentence
        if context.position not in self.cache[context.document.id]:
            return
        
        spans = self.cache[context.document.id][context.position]
        #del self.cache[context.document.id][context.position]
        
        entity_spans = defaultdict(list)
        entity_cids  = {}
        
        # create temp spans
        offsets = [context.document.sentences[i].abs_char_offsets[0] for i in range(len(context.document.sentences))]

        i = context.position
        for tag in spans:
            char_start, char_end = tag.abs_char_start - offsets[i], tag.abs_char_end - offsets[i]
            tc = TemporarySpan(char_start=char_start, char_end=char_end - 1, sentence=context.document.sentences[i])
            tc.load_id_or_insert(self.session)
            entity_cids[tc.id] = tag.concept_uid
            entity_spans[tag.concept_type].append(tc)
        
        # Generates and persists candidates
        candidate_args = {'split' : split}
        for args in product(*[enumerate(entity_spans[et]) for et in self.entity_types]):
            if self.arity == 2:
                ai, a = args[0]
                bi, b = args[1]

                # Check for self-joins, "nested" joins (joins from span to its subspan), 
                # and flipped duplicate "symmetric" relations
                if not self.self_relations and a == b:
                    continue
                elif not self.nested_relations and (a in b or b in a):
                    continue
                elif not self.symmetric_relations and ai > bi:
                    continue

            # Assemble candidate arguments
            for i, arg_name in enumerate(self.candidate_class.__argnames__):
                candidate_args[arg_name + '_id'] = args[i][1].id
                candidate_args[arg_name + '_cid'] = entity_cids[args[i][1].id]
                
            # Checking for existence
            if check_for_existing:
                q = select([self.candidate_class.id])
                for key, value in candidate_args.items():
                    q = q.where(getattr(self.candidate_class, key) == value)
                candidate_id = self.session.execute(q).first()
                if candidate_id is not None:
                    continue
            
            # Add Candidate to session
            yield self.candidate_class(**candidate_args)