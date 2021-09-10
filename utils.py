import pynini

def load_alphabet(source):
    """Load chars from source and add them to a symbol table.

    """
    syms = pynini.SymbolTable()
    syms.add_symbol('ε', 0)
    for symbol in source:
        symbol_id = ord(symbol)
        syms.add_symbol(symbol, symbol_id)
    return syms
