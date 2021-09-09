import argparse
import pynini

""" Tests pynini using the code snippets from Gorman & Sproat (2021),
*Finite-State Text Processing*. """


def main():
    # Build string acceptor
    s = "Godpspeed"
    f = pynini.accep(s, token_type="utf8", weight=2)
    print(f.string(token_type="utf8"))
    
    # Determinize and optimize
    d = pynini.determinize(f)
    d.optimize()
    print(d.string(token_type="utf8"))
    
    # Concat
    d.concat(d)
    d += d # Alternative syntax
    print(d.string(token_type="utf8"))
    
    # Closure
    d.closure() # *-closure, destructive
    f_start = pynini.closure(f) # *-closure, constructive
    f_star = f.star # Alternative syntax
    f_plus = f.plus # +-closure
    f_ques = f.ques # ?-closure

    # Range concatenation
    f4 = f ** 4
    print(f4.string(token_type="utf8"))
    f5to7 = f ** (5,7)
    f3plus = f ** (3, ...)  # Ellipsis represents infinite bound

    # Union
    a = pynini.accep("a")
    bc = pynini.accep("bc")
    d = pynini.accep("d")
    a_bc_d = pynini.union(a, bc, d) # Constructive
    a_bc_d = a | bc | d # Alternative syntax
    a.union(bc).union(d) # Destructive on `a`
    
    # Composition (a generalization of intersection and relation chaining)
    ad = pynini.cross("a", "d")
    bf_star = pynini.cross("b", "f").closure()
    ae = pynini.cross("a", "e")
    t1 = (ad + bf_star) | ae
    t1.rmepsilon()
    di = pynini.cross("d", "i")
    ek = pynini.cross("e", "k")
    fj = pynini.cross("f", "j")
    fl_star = pynini.cross("f", "l").closure()
    t2 = (di + fj).union(ek) + fl_star
    t2.rmepsilon()
    t3 = pynini.compose(t1, t2) # Composition, constructive
    t3 = t1 @ t2 # Alternative syntax
    t3.rmepsilon()
    t3.draw("t3.dot") # To draw this graph, use `dot -Tpng -O t1.dot`

    # Difference (only defined for unweighted languages)
    f1 = pynini.accep('Godspeed') 
    f2 = f1 | pynini.accep('You!')
    f3 = f2 - f1
    print(f3.string(token_type="utf8"))    

    # Cross-product of 2 acceptors
    a1 = pynini.accep("a") | pynini.accep("bc")
    a2 = pynini.accep("de") | pynini.accep("f")
    a3 = pynini.cross(a1, a2)

    # Projection
    t = pynini.cross("ac", "b") | pynini.cross("df", "e")
    t.rmepsilon()
    ip = t.project("input").rmepsilon()
    op = t.project("output").rmepsilon()

    # Inversion
    t.invert() # Destructive
    
    # Reversal
    a = pynini.accep("de") | pynini.accep("abc")
    a.rmepsilon()
    a_rev = pynini.reverse(a)
    return


if __name__ == "__main__":
    main()
