import re
import os
class BrandDetector():
    def __init__(self):
        self.db = None
    def load_brand_list(self,file=None):
        """
        Load the list of brands for the text file and load it as a list of str (self.db). If no file is provided,
        the function will load brands.txt in the Ressources folder
        """
        if not file:
            path = os.path.dirname(os.path.abspath(__file__))
            path = os.path.dirname(path)
            file = os.path.join(path, "Ressources", "brands.txt")
        with open(file, "r") as f:
            self.db = [i for i in f.read().splitlines()]
        self.db.sort(reverse=True,key=len)
    def detect_brand(self,text):
        """
        Detect a brand from the DB within the passed text. The first match will be returned along with its coordinates. 
        If no match is found, return N/A, 0, 0
        """
        for brand in self.db:
            match = re.search(rf"[^a-z0-9]({brand})([^a-z0-9]|$)",text.lower()) 
            if match:
                return (brand,match.start(1),match.end(1))
        return ("N/A", 0, 0)
    def __str__(self):
        if self.db:
            return (f"brand_dectector with {len(self.db)} brands")
        else:
            return("empty brand_detector")
    def __repr__(self):
        return self.__str__()
        
if __name__=="__main__":

    test = BrandDetector()

    test.load_brand_list()
    print("ok",len(test.db))