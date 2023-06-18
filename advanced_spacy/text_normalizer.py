import re
import json
from collections import OrderedDict
from unidecode import unidecode

from advanced_spacy import path_to_special_char

re_patterns = {
    "punctuation_no_dev" : '!"#$%&\'()*+,-.:;<=>?@[\\]^_`{|}~',
    "punctuation_no_math" : '!"#$%&\'(),:;<=>?@[\\]^_`{|}~'
}

def find_unicode(char):
    code_unicode = ord(char)
    code_unicode = hex(code_unicode)
    code_unicode = '\\u' + code_unicode[2:].zfill(4)
    return code_unicode

class TextNormalizer():
    def __init__(self):
        self.special_chars = None
    def load_special_chars(self,file=path_to_special_char):
        with open(file, "r") as f:
            self.special_chars = json.load(f)

    def transform_chars(self,text):
        for c,s in self.special_chars.items():
            while re.search(c,text):
                text = re.sub(c,s,text)
        return text
    
    def remove_html(self,text):
        pattern = re.compile(r"(<[^<#{}]*?>|{[^{]*?})")
        while re.search(pattern,text):
            text = re.sub(pattern," ",text)
        return text
    
   
    def transform(self,text):
        text = self.transform_chars(text)
        text = self.remove_html(text)
        return unidecode(text)
        


class CompositeNumber():
    def __init__(self):
        self.patterns = OrderedDict()
        # Attention : keep real and self.patterns["real"] together. Real does not have the parenthesis
        #to avoid messing up the groups

        real = r"[+-]?\d*[.,]?\d+(?:[eE][+-]?\d+)?"
        self.patterns["real"] = real
        self.patterns["double_x"] = rf"({real}).??[xX].??({real}).??[xX].??({real})"
        self.patterns["simple_x"] = rf"(?:[^xX\d]\s?|^)({real}).??[xX].??({real})(?:\s?[^xX\d]|$)"
        self.patterns["range"] =  rf'({real})\s?\.\.\.\s?({real})|({real})\s?-\s?({real})'
        self.patterns["mix_fraction"] = rf"(\d+)\s(\d+)\s?/\s?(\d+)"
        self.patterns["fraction"] = rf"(?<!\d\s|.\d)(\d+)\s?/\s?(\d+)"

    def evaluate(self,string,pat = None):
        if pat in self.patterns:
            match = re.match(self.patterns[pat] + "$",string)
            if match and pat=="real":
                return [self.real_eval(match.group(0).replace(",", "."))]
            elif match and pat!="real":
                return [self.real_eval(text.replace(",",".")) for text in match.groups() if text]
        else:
            for pat in self.patterns.values():
                match = re.match(pat + r"$", string)
                if match and pat == self.patterns["real"]:
                    return [self.real_eval(match.group(0).replace(",", "."))]
                elif match and pat != self.patterns["real"]:
                    return [self.real_eval(text.replace(",", ".")) for text in match.groups() if text]
        return []

    def real_eval(self,string):
        return float(string.replace(",", "."))






