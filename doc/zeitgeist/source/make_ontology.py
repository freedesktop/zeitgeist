import sys
import os.path
import textwrap

sys.path.insert(0, os.path.abspath('../..'))

from zeitgeist.datamodel import Interpretation, Manifestation

ROWS = ["Children", "URI", "Description", "Python object"]

PAGE_TEMPLATE = """\
======================
The Zeitgeist Ontology
======================

.. _symbol-interpretation:

Interpretations
===============

%(interpretations)s

.. _symbol-manifestation:

Manifestations
==============

%(manifestations)s
"""

def make_line(pattern, columns):
    result = "|"
    for n, size in enumerate(pattern):
        col = " "
        col += columns[n]
        col += " " *(size-len(col))
        assert len(col) == size, "%r, %i != %i" %(col, len(col), size)
        result += "%s|" %col
    return result + "\n"
    
def _wrap_col(column):
    for line in column:
        if not line:
            yield ""
        else:
            for wrapped_line in textwrap.wrap(line, 80):
                yield wrapped_line

def make_row(pattern, columns=None):
    if columns is None:
        result = "+"
        for size in pattern:
            result += "-"*size
            result += "+"
        result += "\n"
    else:
        result = ""
        columns = [col.split("\n") for col in columns]
        columns = [list(_wrap_col(col)) for col in columns]
        max_rows = max(map(len, columns))
        columns = [col + [""]*(max_rows-len(col)) for col in columns]
        for line in zip(*columns):
            result += make_line(pattern, line)
    return result
    
def iter_col_width(col):
    for row in col:
        for line in row.split("\n"):
            yield min(len(line), 80)

def make_table_body(has_header=False, *columns):
    width_pattern = []
    check_rows = None
    for col in columns:
        width_pattern.append(max(iter_col_width(col)) + 2)
        if check_rows is None:
            check_rows = len(col)
        else:
            assert len(col) == check_rows, "all columns must have the same number of rows"
    if has_header:
        table = ""
    else:
        table = make_row(width_pattern)
    for row in zip(*columns):
        table += make_row(width_pattern, row)
        table += make_row(width_pattern)
    return table
    
def make_children(symbol):
    children = symbol.get_children()
    if not children:
        return None
    result = ""
    for child in children:
        result += ":ref:`symbol-%s`,\n" %child.uri.split("/")[-1].lower()
    return result.strip().strip(",")
    
def make_python_path(symbol):
    def _gen(sym):
        yield sym.name
        parents = list(sym.get_parents())
        if parents:
            for s in _gen(parents[0]):
                yield s
    return "``zeitgeist.datamodel.%s``" %".".join(list(_gen(symbol))[::-1])
    
def doc_symbol(symbol, make_ref=True):
    if make_ref:
        result = ".. _symbol-%s:\n\n" %(symbol.uri.split("/")[-1].lower())
    else:
        result = ""
    if symbol.display_name:
        result += "%s\n" %symbol.display_name
        result += "*" *len(symbol.display_name)
        result += "\n\n"
    result += make_table_body(False, ["**%s**" %r for r in ROWS], 
        [make_children(symbol) or "--", symbol.uri, symbol.doc, make_python_path(symbol)]
    )
    return result
    
def gen_symbol_level(symbol, level=0):
    def _gen(symb, lev):
        for child in symb.get_children():
            yield (lev, child.uri)
            for c in _gen(child, lev+1):
                yield c
    children = list(_gen(symbol, level))
    result = dict()
    for n, uri in children:
        result.setdefault(n, []).append(uri)
    max_level = max(result)
    return [result[n] for n in range(max_level+1)]

def create_doc(template):
    values = dict.fromkeys(["interpretations", "manifestations"], "")
    values["interpretations"] += doc_symbol(Interpretation, False)
    values["interpretations"] += "\n"
    for level in gen_symbol_level(Interpretation):
        for uri in sorted(level):
            values["interpretations"] += doc_symbol(Interpretation[uri])
            values["interpretations"] += "\n"

    values["manifestations"] += doc_symbol(Manifestation, False)
    values["manifestations"] += "\n"
    for level in gen_symbol_level(Manifestation):
        for uri in sorted(level):
            values["manifestations"] += doc_symbol(Manifestation[uri])
            values["manifestations"] += "\n"
    return template %values

if __name__ == "__main__":
    if len(sys.argv) == 1:
        template = PAGE_TEMPLATE
    elif len(sys.argv) == 2:
        template = file(sys.argv[1]).read()
    else:
        raise ValueError
    print create_doc(template)
