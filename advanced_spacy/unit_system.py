import sympy as sp
import json
import os
from itertools import chain
from advanced_spacy import path_to_units

prefixes = {
    # 'quetta': 10**30,
    # 'ronna': 10**27,
    # 'yotta': 10**24,
    # 'zetta': 10**21,
    # 'exa': 10**18,
    # 'peta': 10**15,
    # 'tera': 10**12,
    'giga': 10**9,
    'mega': 10**6,
    'kilo': 10**3,
    'hecto': 10**2,
    'deca': 10**1,
    'deci': 10**-1,
    'centi': 10**-2,
    'milli': 10**-3,
    'micro': 10**-6,
    'nano': 10**-9,
    'pico': 10**-12,
    # 'femto': 10**-15,
    # 'atto': 10**-18,
    # 'zepto': 10**-21,
    # 'yocto': 10**-24,
    # 'ronto': 10**-27,
    # 'quecto': 10**-30,
    # 'Q': 10**30,
    # 'R': 10**27,
    # 'Y': 10**24,
    # 'Z': 10**21,
    # 'E': 10**18,
    # 'P': 10**15,
    # 'T': 10**12,
    'G': 10**9,
    'M': 10**6,
    'k': 10**3,
    'K': 10**3,
    'h': 10**2,
    'da': 10**1,
    'd': 10**-1,
    'c': 10**-2,
    'm': 10**-3,
    'micro': 10**-6, #µ
    'n': 10**-9,
    'p': 10**-12,
    # 'f': 10**-15,
    # 'a': 10**-18,
    # 'z': 10**-21,
    # 'y': 10**-24,
    # 'r': 10**-27,
    # 'q': 10**-30
}
for i in list(prefixes.keys()):
    if len(i)>2:
        prefixes[i.capitalize()]=prefixes[i]
        prefixes[i.upper()]=prefixes[i]


class Measure():
    def __init__(self):
        self.name = ""
        self.base = ""
        self.value = sp.Symbol(self.name + "(unit)")
        self.conversions = dict()
        self.alias = dict()
        self.prefixes = prefixes

    def get_unit(self, unit):
        """
        Returns a tuple containing the value of the prefix (or 1 if there's no prefix) and the
        key for the conversion dictionnary. If no match is found return None,None
        """
        if unit in self.alias:
            return 1, self.alias[unit]
        for i in self.prefixes:
            if unit[:len(i)] == i:
                pre = self.prefixes[i]
                return pre, self.alias[unit[len(i):]]
        return None, None

    def to_base(self, value, unit):
        """
        Converts the value in unit in the base unit of this measure object.
        """
        p, u = self.get_unit(unit)
        return float(self.conversions[u].subs(self.value, value) * p)

    def string_to_base(self, string, unit, power):
        """
        Evaluate the string as a value expressed in unit^power and convert to base unit^power
        """
        value = eval(string.replace(",", "."))
        value = value ** (1 / power)
        value = self.to_base(value, unit) ** power
        return value

    def to_unit(self, value, unit):
        """
        Converts the value expressed in the base unit of this measure object into the unit passed as argument.
        """
        p, u = self.get_unit(unit)
        base_val = sp.Symbol("base")
        return float(sp.solve(sp.Eq(out, p * self.conversions[u]), self.value)[0].subs(base_val, value))

    def unit_to_unit(self, value, unit_src, unit_tgt):
        """
        Converts the value expressed in unit_src into unit_tgt
        """
        p_src, u_src = self.get_unit(unit_src)
        p_tgt, u_tgt = self.get_unit(unit_tgt)
        v_base = p_src * self.conversions[u_src].subs(self.value, value)
        return float(sp.solve(sp.Eq(v_base, p_tgt * self.conversions[u_tgt]))[0])

    def save(self, filename):
        """
        Save the current measure in json format in a text file
        """
        conv = dict([(key, str(value.subs(self.value, "q"))) for key, value in self.conversions.items()])
        dico = {"name": self.name, "base": self.base, "conversions": conv, "alias": self.alias}
        with open(filename, "w") as f:
            json.dump(dico, f, indent=4, ensure_ascii=False)

    def load(self, filename):
        """
        Load the data contained in a json text file into the current object
        """
        with open(filename, "r") as f:
            dico = json.load(f)
        self.name = dico['name']
        self.base = dico['base']
        self.value = sp.Symbol(self.name + "(unit)")
        self.alias = dico['alias']
        self.conversions = dict(
            [(key, sp.sympify(value).subs(sp.Symbol("q"), self.value)) for key, value in dico['conversions'].items()])
        for key in self.conversions:
            self.alias[key]=key

    def expand(self, min_len=None):  # !!! not for symbol of len 1 or 2
        """
        Generate capitalize and upper aliases
        """
        if not min_len:
            min_len = 2
        temp = list(self.alias.keys())
        for i in temp:
            if len(i) > min_len:
                self.alias[i.capitalize()] = self.alias[i]
                self.alias[i.upper()] = self.alias[i]

    def all_alias(self):
        """
        Return a generator of all alias present in this measure combined with all prefixes. 
        """
        return (i + j for i in [""] + list(self.prefixes.keys()) for j in self.alias)
        # return chain((i + j for i in [""] + list(self.prefixes.keys()) for j in self.alias),
        #              (i + j + "s" for i in [""] + list(self.prefixes.keys()) for j in self.alias if len(i+j)>=2))

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.name}- base:{self.base}, #units:{len(self.conversions)}, #alias:{len(self.alias)}"


class UnitSystem():
    def __init__(self):
        self.measures = dict()
        self.complex_measures = {
            "volume": ("longueur", 3),
            "surface": ("longueur", 2)
        }

    def load_measures(self, directory=path_to_units):
        for filename in os.listdir(directory):
            if filename.endswith(".txt"):
                mes = Measure()
                mes.load(os.path.join(directory, filename))
                mes.expand()
                self.measures[mes.name] = mes
        # we remove doublons like m3 which would be generated by complex measure volume
        # and the simple measure volume
        for cm in self.complex_measures:
            sm = self.complex_measures[cm][0]
            pow = self.complex_measures[cm][1]
            for key in self.measures[sm].alias:
                if key + str(pow) in self.measures[cm].alias:
                    self.measures[cm].alias.pop(key + str(pow))

    def all_complex_alias(self,complex_measure):
        """
        return all aliases of a complex measure (not including the non complex units. For 'volume', m3
        will be included but not litre)
        """
        if complex_measure in self.complex_measures:
            m = self.complex_measures[complex_measure][0]
            pow = self.complex_measures[complex_measure][1]
            return ( i + str(pow) for i in self.measures[m].all_alias())
    def all_base_complex_alias(self,complex_measure):
        """
        Return all alias of complex measure without prefix. This does not include non-complex units
        like hectare or litre.
        """
        if complex_measure in self.complex_measures:
            m = self.complex_measures[complex_measure][0]
            pow = self.complex_measures[complex_measure][1]
        return ( i + str(pow) for i in self.measures[m].alias.keys())

    def all_alias(self):
        """
        return all aliases of complex and simple meausre
        """
        alias = (a for u in self.measures.values() for a in u.all_alias())
        alias = chain(alias,(a for cm in self.complex_measures for a in self.all_complex_alias(cm)))
        return alias

    def __str__(self):
        return "[" + ",".join(self.measures.keys()) + "]"

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, key):
        return self.measures[key]

    def __iter__(self):
        self.key_generator = iter(self.measures.values())
        return self

    def __next__(self):
        return next(self.key_generator)