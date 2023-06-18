import sys
import os

import spacy
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import advanced_spacy
from spacy.tokens import Token,Doc,Span, SpanGroup
from spacy.matcher import Matcher, PhraseMatcher
from spacy.language import Language
from spacy.tokenizer import Tokenizer







