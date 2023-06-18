import spacy
from spacy.tokens import Doc, SpanGroup, Span
from IPython.display import clear_output,display
from IPython.display import HTML as html_print
import warnings

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

