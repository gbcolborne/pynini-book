import argparse
import pynini

""" Tests pynini using the code snippets from Gorman & Sproat (2021),
*Finite-State Text Processing*. """


def main():
    # Empty FST
    f = pynini.Fst()
    assert f.start() == pynini.NO_STATE_ID
    
    # Build string acceptor
    s = "Godpspeed"
    f = pynini.accep(s, token_type="utf8", weight=2)
    print(f.string(token_type="utf8"))
    print(f.string(token_type="byte"))
          
    # Check some properties
    assert f.arc_type() == "standard"
    assert f.weight_type() == "tropical"
    assert f.start() != pynini.NO_STATE_ID    
    f.final(8) == pynini.Weight.zero(f.weight_type()) # State 8 is not final 
    f.final(9) != pynini.Weight.zero(f.weight_type()) # State 9 is final    
    assert f.properties(pynini.CYCLIC, True) != pynini.CYCLIC # f is not cyclic
    assert f.properties(pynini.CYCLIC, False) != pynini.CYCLIC # f is not known to be cyclic
    ua_props = pynini.ACCEPTOR | pynini.WEIGHTED
    assert f.properties(ua_props, True) == ua_props # f is a weighted acceptor
    assert f.verify() # f's properties are correct
    
    # Convert to log semiring
    g = pynini.arcmap(f, map_type="to_log")
    assert g.arc_type() == "log"
    assert g.weight_type() == "log"

    # Check weights of tropical and log semirings
    print(pynini.Weight.zero(f.weight_type()))
    print(pynini.Weight.zero(g.weight_type()))
    print(pynini.Weight.one(f.weight_type()))
    print(pynini.Weight.one(g.weight_type()))

    # Build transducer using `string_map`
    m = [
            ("AL", "Alabama"),
            ("AK", "Alaska"),
            ("AR", "Arkansas"),
            ("AZ", "Arizona")
        ]
    f = pynini.string_map(m)
    assert f.properties(pynini.CYCLIC, True) != pynini.CYCLIC # f is not cyclic
    
    # Check paths, strings, labels, weights
    paths = f.paths(output_token_type='utf8')
    print(list(paths.istrings()))
    paths.reset()
    print(list(paths.ostrings()))
    paths.reset()    
    while not paths.done():
        print("{}\t{}\t{}\t{}\t{}".format(paths.ilabels(),
                                          paths.istring(),
                                          paths.olabels(),
                                          paths.ostring(),
                                          paths.weight()))
        paths.next()

    # Create another FST by sampling paths from f
    g = pynini.randgen(f,npath=2,select='log_prob')
    paths = g.paths(output_token_type='utf8')
    print(list(paths.istrings()))
    paths.reset()
    print(list(paths.ostrings()))
    return


if __name__ == "__main__":
    main()
