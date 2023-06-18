import os
path_to_root = os.path.dirname(os.path.abspath(__file__))
path_to_brands = os.path.join(os.path.dirname(path_to_root), "Ressources", "brands.txt")
path_to_special_char = os.path.join(os.path.dirname(path_to_root), "Ressources", "special_char.txt")
path_to_units = os.path.join(os.path.dirname(path_to_root), "Ressources","Unit system")
import sys
sys.path.append(path_to_root)
from . import brands, custom_pipeline,custom_visualization,text_normalizer,unit_system

