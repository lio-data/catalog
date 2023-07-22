import json
import spacy

class MatcherRuleMaker():
    def __init__(self):
        self.rules = None

    def load(self,path):
        with open(path,'rt') as f:
            self.rules = json.load(f)
        self.normalize_rules()

    def normalize_rules(self):
        normalized_rules = dict()
        for item in self.rules:
            norm_pattern_list = []
            pattern_list = self.rules[item]["rules"]
            description = self.rules[item]["desc"]
            for pattern in pattern_list:
                temp_list = [[]]
                for dico in pattern:
                    n = len(self.list_normalized_dico(dico))
                    m = len(temp_list)
                    temp_list = [l.copy() for l in temp_list for _ in self.list_normalized_dico(dico)]
                    for i in range(n * m):
                        index = i % n
                        temp_list[i].append(self.list_normalized_dico(dico)[index])
                for i in temp_list:
                    norm_pattern_list.append(i)
            normalized_rules[item] = {"desc" : description,"rules" : norm_pattern_list}
        self.rules = normalized_rules


    def list_normalized_dico(self,dico):
        out = [dict()]
        for key,value in dico.items():
            if "OPTION" in key :
                options_key_val = list(value.items())
                n = len(options_key_val)
                m = len(out)
                out = [i.copy() for i in out for _ in range(n)]
                for i in range(n*m):
                    index = i%n
                    out[i][options_key_val[index][0]] = options_key_val[index][1]
            else:
                for dico in out:
                    dico[key] = value
        return out

    def __str__(self):
        out = """"""
        for r in self.rules:
            out += r + "\n"
            out += self.rules[r]['desc'] + "\n"
            for p in self.rules[r]['rules']:
                out += str(p) + "\n"
        return out


if __name__ == "__main__":
    mrm = MatcherRuleMaker()
    mrm.load("../Ressources/matcher.json")
    print("#####################")
    print(mrm)
    
    # print(mrm.list_normalized_dico({"IS_SENT_START": False, "OP": "{0,9}", "OPTIONS1":{"LIKE_NUM":True, "IS_ALPHA":True},
    #                                 "OPTIONS2":{"A":1,"B":2}
    #                                 }))

    
    


            