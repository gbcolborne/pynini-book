import argparse
import pynini
from pynini.lib import pynutil


""" Tests pynini using the code snippets from Gorman & Sproat (2021),
*Finite-State Text Processing*. """

def run_t9():
    """  T9 typing. """
    t9_map = [
        ("0", [" "]),
        ("2", ["a", "b", "c"]),
        ("3", ["d", "e", "f"]),
        ("4", ["g", "h", "i"]),
        ("5", ["j", "k", "l"]),
        ("6", ["m", "n", "o"]),
        ("7", ["p", "q", "r", "s"]),
        ("8", ["t", "u", "v"]),
        ("9", ["w", "x", "y", "z"]),
    ]
    decoder = pynini.Fst()
    for (inp, outs) in t9_map:
        decoder.union(pynini.cross(inp, pynini.union(*outs)))
    decoder.closure().optimize()

    # Create a lexicon to restrict output
    lexicon = ["ball", "cat", "request", "pervert"]
    lprime = pynutil.join(pynini.string_map(lexicon), " ")

    # Test decoder
    istring = pynini.accep("7378378")
    olattice = istring @ decoder @ lprime
    olattice.optimize()
    ostrings = list(olattice.paths().ostrings())
    print(ostrings)
    
def main():
    run_t9()
    return


if __name__ == "__main__":
    main()



