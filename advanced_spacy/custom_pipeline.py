import spacy
from spacy.tokens import Token,Doc,Span, SpanGroup
from spacy.matcher import Matcher, PhraseMatcher
from spacy.language import Language
from spacy.tokenizer import Tokenizer

import re
import regex

Doc.set_extension("label",default=None)
Doc.set_extension("brand",default="N/A")
Token.set_extension("is_unit",default=False)
Token.set_extension("is_cn",default=False)

from brands import BrandDetector
brand_detect = BrandDetector()
brand_detect.load_brand_list()

from text_normalizer import TextNormalizer, CompositeNumber
text_norm = TextNormalizer()
text_norm.load_special_chars()
cn = CompositeNumber()


from unit_system import UnitSystem, Measure, prefixes
unit_sys = UnitSystem()
unit_sys.load_measures()

class CustomTokenizer(Tokenizer):
    def __init__(self,vocab):
        print("Custom Tokenizer instantiated:",len(vocab),"words in vocab -", len(text_norm.special_chars),"special chars")
        super().__init__(vocab)
    def __call__(self, text):
        text = text_norm.transform(text)
        doc = super().__call__(text)
        doc._.brand = brand_detect.detect_brand(doc.text)[0]
        return doc


@spacy.registry.tokenizers("custom_tokenizerv1")
def create_tokenizer_factory():
    def create_tokenizer(nlp2):
        nlp = spacy.load("fr_core_news_lg")
        tokenizer = CustomTokenizer(nlp.vocab)

        split_list = [r"\(", r"\)", r"\[", r"\]", r":"]
        unit_split_list = [rf"(?<=^\d){alias}s?" for alias in unit_sys.all_alias()]
        unit_split_list += [rf"(?<=\d\d|\.\d){alias}s?" for alias in unit_sys.all_alias()]

        prefix_re = nlp.Defaults.prefixes + split_list
        infix_re = nlp.Defaults.infixes + split_list  # + unit_split_list
        suffix_re = nlp.Defaults.suffixes + split_list + unit_split_list
        tokenizer.prefix_search = spacy.util.compile_prefix_regex(prefix_re).search
        tokenizer.infix_finditer = spacy.util.compile_infix_regex(infix_re).finditer
        tokenizer.suffix_search = spacy.util.compile_suffix_regex(suffix_re).search
        return tokenizer
    return create_tokenizer

@Language.component("preprocess")
def preprocess_doc(doc):
    """
    Ensure the sentences are split after \n and . Also ensure that composite numbers
    are grouped in a single token
    """
    for token in doc[:-1]:
        if token.text=="\n" or (token.text=="." and doc[token.i+1].text!=": "):
            doc[token.i+1].is_sent_start = True
        else:
            doc[token.i+1].is_sent_start = False
    for n,p in cn.patterns.items():
        if n!="real":
            for m in re.finditer(p,doc.text):
                l = len(m.groups())
                b= min([m.start(i) for i in range(1,l+1) if m.group(i)])
                e= max([m.end(i) for i in range(1,l+1) if m.group(i)])
                to_merge = [t.i for t in doc if t.idx>=b and t.idx<e ]
                if to_merge:
                    with doc.retokenize() as retok:
                        retok.merge(Span(doc,to_merge[0],to_merge[-1]+1))
    return doc

class BrandUnitMarker():
    def __init__(self, nlp):
        self.nlp = nlp

    def __call__(self, doc):
        """
        Detect the brand (doc) and mark all instances of the brand, detect all units and
        composite numbers
        """
        matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        pattern = Doc(self.nlp.vocab, words=doc._.brand.split())
        matcher.add("BRAND", [pattern])
        list_spans = []
        tokens_detected = set()
        # temp_nlp = spacy.blank("fr")
        # detect brand
        for match_id, start, end in matcher(doc):
            span = Span(doc, start, end, label="BRAND")
            if span and all([(t.i not in tokens_detected) for t in span]):
                tokens_detected = tokens_detected.union(set([t.i for t in span]))
                list_spans = list_spans + [span]
        #detect complex measure
        for cm in unit_sys.complex_measures:
            if any([alias in doc.text] for alias in unit_sys.all_base_complex_alias(cm)):
                #before checking all alais with prefix we first check if at least one of the base alias is in the text
                matcher = PhraseMatcher(self.nlp.vocab)
                patterns = [self.nlp.make_doc(alias) for alias in unit_sys.all_complex_alias(cm) if alias in doc.text]
                matcher.add(cm, patterns)
                for match_id, start, end in matcher(doc):
                    span = Span(doc, start, end, label=cm)
                    span[0]._.is_unit = True
                    if span and all([t.i not in tokens_detected for t in span]):
                        tokens_detected = tokens_detected.union(set([t.i for t in span]))
                        list_spans = list_spans + [span]
        for u in unit_sys:
            base_alias = [alias for alias in u.alias.keys() if alias in doc.text]
            matcher = PhraseMatcher(self.nlp.vocab)
            patterns = [self.nlp.make_doc(alias) for alias in [p+a for p in [""] + list(prefixes.keys()) for a in base_alias]]
            matcher.add(u.name, patterns)
            for match_id, start, end in matcher(doc):
                span = Span(doc, start, end, label=u.name)
                span[0]._.is_unit = True
                if span and all([t.i not in tokens_detected for t in span]):
                    tokens_detected = tokens_detected.union(set([t.i for t in span]))
                    list_spans = list_spans + [span]
        for name, patt in cn.patterns.items():
            if name != "real":
                for m in re.finditer(patt, doc.text):
                    l = len(m.groups())
                    b = min([m.start(i) for i in range(1, l + 1) if m.group(i)])
                    e = max([m.end(i) for i in range(1, l + 1) if m.group(i)])
                    span_token = [t.i for t in doc if t.idx >= b and t.idx < e]
                    if span_token and all([i not in tokens_detected for i in span_token]):
                        doc[span_token[0]]._.is_cn = True
                        tokens_detected = tokens_detected.union(set(span_token))
                        list_spans = list_spans + [Span(doc, min(span_token), max(span_token) + 1, label="cn_" + name)]
        doc.ents = list_spans
        return doc

@Language.factory("brand_unit_numbers")
def create_brand_unit_marker(nlp, name):
     return BrandUnitMarker(nlp)

class BrandUnitMarkerv2():
    def __init__(self, nlp):
        self.nlp = nlp
        self.matchers = dict()
        self.doc_maker = spacy.blank("fr")
        self.create_matchers()

    def create_matchers(self):
        for cm in unit_sys.complex_measures:
            self.matchers[cm] = PhraseMatcher(self.nlp.vocab)
            patterns = [self.doc_maker.make_doc(alias + s) for alias in unit_sys.all_complex_alias(cm) for s in ["","s"]]
            self.matchers[cm].add(cm, patterns)
        for name, unit in unit_sys.measures.items():
            if not name in self.matchers:
                self.matchers[name] = PhraseMatcher(self.nlp.vocab)
            patterns = [self.doc_maker.make_doc(alias + s) for alias in unit.all_alias() for s in ["","s"]]
            self.matchers[name].add(name, patterns)

    def __call__(self, doc):
        """
        Detect the brand (doc) and mark all instances of the brand, detect all units and
        composite numbers
        """
        matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        pattern = Doc(self.nlp.vocab, words=doc._.brand.split())
        matcher.add("BRAND", [pattern])
        list_spans = []
        tokens_detected = set()
        # detect brand
        for match_id, start, end in matcher(doc):
            span = Span(doc, start, end, label="BRAND")
            if span and all([(t.i not in tokens_detected) for t in span]):
                tokens_detected = tokens_detected.union(set([t.i for t in span]))
                list_spans = list_spans + [span]
        #detect complex measure
        for cm in unit_sys.complex_measures:
            for match_id, start, end in self.matchers[cm](doc):
                span = Span(doc, start, end, label=cm)
                span[0]._.is_unit = True
                if span and all([t.i not in tokens_detected for t in span]):
                    tokens_detected = tokens_detected.union(set([t.i for t in span]))
                    list_spans = list_spans + [span]
        #detect simple units
        for u in unit_sys:
            # if any([alias in doc.text for alias in u.conversions]):
            for match_id, start, end in self.matchers[u.name](doc):
                span = Span(doc, start, end, label=u.name)
                span[0]._.is_unit = True
                if span and all([t.i not in tokens_detected for t in span]):
                    tokens_detected = tokens_detected.union(set([t.i for t in span]))
                    list_spans = list_spans + [span]
        #detect composite numbers
        for name, patt in cn.patterns.items():
            if name != "real":
                for m in re.finditer(patt, doc.text):
                    l = len(m.groups())
                    b = min([m.start(i) for i in range(1, l + 1) if m.group(i)])
                    e = max([m.end(i) for i in range(1, l + 1) if m.group(i)])
                    span_token = [t.i for t in doc if t.idx >= b and t.idx < e]
                    if span_token and all([i not in tokens_detected for i in span_token]):
                        doc[span_token[0]]._.is_cn = True
                        tokens_detected = tokens_detected.union(set(span_token))
                        list_spans = list_spans + [Span(doc, min(span_token), max(span_token) + 1, label="cn_" + name)]
        doc.ents = list_spans
        return doc

@Language.factory("brand_unit_numbersv2")
def create_brand_unit_markerv2(nlp, name):
     entity_ruler = BrandUnitMarkerv2(nlp)
     return entity_ruler

class FalsePositiveUnit():
    def __init__(self, nlp):
        self.nlp = nlp
    def __call__(self, doc):
        """
        Remove tokens that were wrongly marked as units. Remove it frome ents and put
        token._.is_unit to False
        """
        for s in doc.sents:
            i_min, i_max = s.start, s.end
            if any([t._.is_unit for t in s]) and not any([t._.is_cn or t.like_num for t in s]):
                for t in s:
                    t._.is_unit = False
                for e in doc.ents:
                    if e.start >= i_min and e.end <= i_max:
                        ents = list(doc.ents)
                        ents.remove(e)
                        doc.ents = ents
        return doc

@Language.factory("false_positive_unit_cleaner")
def create_false_positive_unit_cleaner(nlp, name):
     return FalsePositiveUnit(nlp)

@spacy.registry.callbacks("feed_vocabulary")
def make_feed_vocabulary():
    def feed_vocabulary(nlp):
        test = nlp(" ".join(["cn_"  + i for i in cn.patterns.keys()]))
        
    return feed_vocabulary