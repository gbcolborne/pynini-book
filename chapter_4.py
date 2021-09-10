import argparse
import pynini
from pynini.lib import pynutil
from utils import load_alphabet

""" Tests pynini using the code snippets from Gorman & Sproat (2021),
*Finite-State Text Processing*. """


def main():                           
    ac = pynini.cross('a', 'c')
    bb = pynini.cross('b', 'b')
    bc = pynini.cross('b', 'c')
    cb = pynini.cross('c', 'b')
    cc = pynini.cross('c', 'c')
    da = pynini.cross('d', 'a')    
    db = pynini.cross('d', 'b')
    t1 = ac + (cb | db)
    t2 = cc + (cb | db)
    t3 = bc + (cb | db)
    t4 = db + da
    t5 = bb + da
    t = t1 | t2 | t3 | t4 | t5    
    t.rmepsilon()

    # Draw 
    syms = load_alphabet(['a','b','c','d','e'])    
    t.draw("t.dot", isymbols=syms, osymbols=syms)

    # Optimize
    t.optimize()
    t.draw("t_opt.dot", isymbols=syms, osymbols=syms)

    # Make a weighted acceptor
    a = pynutil.add_weight(pynini.accep("a"), 2).star
    b = pynutil.add_weight(pynini.accep("b"), 3)
    c = pynutil.add_weight(pynini.accep("c", 3), 4) # Final weight 3, path weight 4 
    d = pynutil.add_weight(pynini.accep("d"), 5)
    e = pynutil.add_weight(pynini.accep("e", 3), 4) # Final weight 3, path weight 4 
    f = a + ((b + c) | (d + e))
    f.optimize()
    f.draw("f.dot", isymbols=syms, osymbols=syms)

    # Get shortest paths
    sp = pynini.shortestpath(f, nshortest=2)
    sp.rmepsilon()
    sp.draw("sp.dot", isymbols=syms, osymbols=syms)
    return


if __name__ == "__main__":
    main()
