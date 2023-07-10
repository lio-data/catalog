import os
import warnings
import datetime

import spacy
from spacy.tokens import Doc, SpanGroup, Span
from IPython.display import clear_output,display
from IPython.display import HTML as html_print

from advanced_spacy import path_to_root, path_to_template


def html_export(doc_list,to_print, path = None):
    """
    Export to path the visualization of the list of documents (doc_list). to_print lists all desired visualizations.
    If path is not specified it will be exported in the folder visualization.
    to_print is a list listing the desired visualiztions and optionnaly arguments grouped as tuples:
    - "token" : no argument. Highlight the toekn separation with a colored |
    - "ent" : no argument. Highlight the named entities
    - "attribute" : expect a tuple (argument,value). Highlight tokens with the attribute == value
    """
    if not path:
        # path = os.path.join(path_to_root,"visualisations")
        now = datetime.datetime.now()
        path = os.path.join("visualisations" ,f"Export_{now.month}-{now.day}@{now.hour}h{now.minute}.html")

    html_output=""
    keys = [str(i+1) + " " + x[0] for i,x in enumerate(to_print)]
    for j,item in enumerate(to_print):
        sub = keys[j]
        if 'token' in sub:
            for i,doc in enumerate(doc_list):
                html_output += generate_banner(sub, keys, i)
                for t in doc:
                    if t.text == "\n":
                        html_output += " <b style='background-color: #f6b73c'> | </b> <br>"
                    else:
                        html_output += t.text_with_ws + " <b style='background-color: #f6b73c'> | </b> "
                html_output += "<hr>"
        if "ent" in sub:
            for i,doc in enumerate(doc_list):
                html_output += generate_banner(sub, keys, i)
                html_output += spacy.displacy.render(doc, style="ent",jupyter=False)
                html_output += "<hr>"
        if "attribute" in sub:
            att, value = item[1],item[2]
            for i,doc in enumerate(doc_list):
                html_output += generate_banner(sub, keys, i)
                html_output += f"<h3>{att}=={value}</h3>"
                for t in doc:
                    text = t.text_with_ws.replace('\n', '<br>')
                    if getattr(t, att) == value:
                        html_output += f"<b style='background-color: #22e664'>{text}</b>"
                    else:
                        html_output += text
                html_output += "<hr>"

        if "extension" in sub:
            att, value = item[1], item[2]
            for i,doc in enumerate(doc_list):
                html_output += generate_banner(sub, keys, i)
                html_output += f"<h3>._{att}=={value}</h3>"
                for t in doc:
                    text = t.text_with_ws.replace('\n', '<br>')
                    if getattr(t._, att) == value:
                        html_output += f"<b style='background-color: #ee3333'>{text}</b>"
                    else:
                        html_output += text
                html_output += "<hr>"
        if 'spans' in sub:
            spans_key, spans_label = item[1], item[2]
            colors = [f'rgb({(255 + i * 51) % 256},{(i * 3 * 51) % 256},{(i * 2 * 51) % 256})' for i in
                      range(len(spans_label))]
            colors = dict(zip(spans_label, colors))
            for i,doc in enumerate(doc_list):
                html_output += generate_banner(sub, keys, i)
                html_output += f"<h3>{spans_key}:{spans_label}</h3>"
                for sent in doc.sents:
                    temp_doc = Doc(doc.vocab, [t.text for t in sent])
                    sg = SpanGroup(temp_doc, name=spans_key, spans=[])
                    for sp in doc.spans[spans_key]:
                        if sp.start >= sent.start and sp.end <= sent.end:
                            temp_span = Span(temp_doc, sp.start - sent.start, sp.end - sent.start, label=sp.label)
                            sg.append(temp_span)
                    temp_doc.spans[spans_key] = sg
                    html_output += spacy.displacy.render(temp_doc, style="span", jupyter=False,
                                                         options={"spans_key": spans_key, "colors": colors,
                                                                  "compact": False})
                html_output += "<hr>"
        if 'dep' in sub:
            for i, doc in enumerate(doc_list):
                html_output += generate_banner(sub, keys, i)
                temp_doc = list(doc.sents)
                html_output += spacy.displacy.render(temp_doc, jupyter=False)
                html_output += "<hr>"

    with open(path_to_template,"rt") as f:
        template = f.read()
    with open(path,"wt") as f:
        f.write(template.replace("#HTML_INPUT",html_output))

def get_html_title(sub):
    titles = {
        "token": "Tokenization",
        "ent": "Named Entities",
        "attribute" : "Attribute",
        "extension" : "Custom Attribute",
        "spans" : "Doc Span",
        "dep" : "POS and DEP"
    }
    sub = sub.split()
    return sub[0]+"-"+titles[sub[1]]

def generate_banner(sub, subjects,i):
    banner = f"<a id=\"{sub}_{i}\"></a>"
    banner += f"<h2>{get_html_title(sub)} Document{i}</h2>"
    for s in subjects:
        banner += f"<a href=\"#{s}_{i}\">{get_html_title(s)}</a> "
    banner+="<br>"
    return banner


    

def multi_displacy(doc_list,style="ent"):
    """
    Call multiple times displacy on the doc list and provide the possibility to exit the viewer. Will show the ent
    by default
    """
    for doc in doc_list:
        clear_output()
        spacy.displacy.render(doc, style=style)
        if input("Type 's' when you want to stop the visualization") == "s":
            break


def visualize_tokenization(doc_list):
    """
    Visualize the tokenization of all doc in doc_list.
    """
    for doc in doc_list:
        out = ""
        clear_output()
        for t in doc:
            if t.text == "\n":
                out = out + " <b style='background-color: #ff0000'> | </b> <br>"
            else:
                out = out + t.text_with_ws + " <b style='background-color: #ff0000'> | </b> "
        display(html_print(out))
        if input("Type 's' when you want to stop the visualization") == "s":
            break


def visualize_attribute(doc_list,attribute,value):
    """
    Visualize all docs and highlight token with attribute = value
    """
    for doc in doc_list:
        clear_output()
        out = ""
        for t in doc:
            text = t.text_with_ws.replace('\n','<br>')
            if getattr(t,attribute) == value:
                out = out + f"<b style='background-color: #11ff11'>{text}</b>"
            else:
                out = out + text
        display(html_print(out))
        if input("Type 's' when you want to stop the visualization") == "s":
            break

def visualize_extension(doc_list,extension,value):
    """
    Visualize all docs and highlight token with ._.extension = value
    """
    for doc in doc_list:
        clear_output()
        out = ""
        for t in doc:
            text = t.text_with_ws.replace('\n','<br>')
            if getattr(t._,extension) == value:
                out = out + f"<b style='background-color: #1111ff'>{text}</b>"
            else:
                out = out + text
        display(html_print(out))
        if input("Type 's' when you want to stop the visualization") == "s":
            break

def visualize_docspan(doc_list,spans_key,span_label):
    """
    Visualize all doc.spans[span_keys] in all docs and highlight spans with label in the span_label list
    """
    colors = [f'rgb({(255+i*51)%256},{(i*3*51)%256},{(i*2*51)%256})' for i in range(len(span_label))]
    colors = dict(zip(span_label,colors))
    warnings.filterwarnings("ignore")
    for doc in doc_list:
        clear_output()
        for sent in doc.sents:
            temp_doc = Doc(doc.vocab,[t.text for t in sent])
            sg = SpanGroup(temp_doc,name=spans_key,spans=[])
            for sp in doc.spans[spans_key]:
                if sp.start >=sent.start and sp.end <= sent.end:
                    temp_span = Span(temp_doc, sp.start - sent.start, sp.end - sent.start, label=sp.label)
                    sg.append(temp_span)
            temp_doc.spans[spans_key] = sg
            spacy.displacy.render(temp_doc, style="span", jupyter=True,
                                  options={"spans_key": spans_key, "colors": colors,
                                           "compact": False})
        if input("Type 's' when you want to stop the visualization") == "s":
            break
    warnings.filterwarnings("default")



def visualize_dep(doc):
    """
    Visualize all sents (4 by 4) in compact mode
    """
    for i in range(len(list(doc.sents))//4) :
        clear_output
        for s in list(doc.sents)[4*i:4*(i+1)]:
            spacy.displacy.render(s, options={"compact": True})
        if input("Type 's' when you want to stop the visualization") == "s":
            break

