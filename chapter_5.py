import argparse
from typing import Iterable, Optional
import pynini
from pynini.lib import pynutil, rewrite, byte
from utils import load_alphabet

""" Tests pynini using the code snippets from Gorman & Sproat (2021),
*Finite-State Text Processing*. """


SPANISH_ALPHABET = pynini.union(
    'a', 'á', 'b', 'c', 'd', 'e', 'é', 'f', 'g', 'h', 'i', 'í',
    'j', 'k', 'l', 'm', 'n', 'ñ', 'o', 'ó', 'p', 'q', 'r', 's',
    't', 'u', 'ú', 'ü', 'v', 'w', 'x', 'y', 'z'
)

SPANISH_PHONEMES = pynini.union(
    'a', 'b', 'd', 'e', 'f', 'g', 'i', 'j', 'k', 'l', 'ʝ', 'm',
    'n', 'ɲ', 'o', 'p', 'r', 'ɾ', 's', 'ʃ', 't', 'u', 'w', 'x', 'z'
)


def run_basics():
    # Compile rule (3), i.e. (b -> a / b__b), for simultaneous
    # application. Note: the first four arguments of `cdrewrite`, all
    # mandatory, include: a transducer representing the rewrite rule,
    # the left and right contexts (which may be the empty string, then
    # a cyclic, unweighted acceptor that defines sigma^*, the closure
    # over the rule's alphabet.
    sigma_star = pynini.union('a', 'b', 'c').closure()
    rule3 = pynini.cdrewrite(
        pynini.cross('b', 'a'),
        'b',
        'b',
        sigma_star,
        'sim'
    )

    # Compile rule (8), i.e. (b -> a / ^b__b), for left-to-right
    # application, which is the default.
    rule8 = pynini.cdrewrite(
        pynini.cross('b', 'a'),
        '[BOS]b',
        'b',
        sigma_star
    )

    # Construct a lattice of output strings for both rules, by
    # composing an input string acceptor with the rule.
    string = pynini.accep('b') ** (3,7) # b{3,7}
    lattice3 = string @ rule3
    lattice8 = string @ rule8

    # Make sure the lattice automata are not empty
    assert lattice3.start() != pynini.NO_STATE_ID
    assert lattice8.start() != pynini.NO_STATE_ID    

    # Convert these transducers to acceptors over output strings
    lattice3.project('output').rmepsilon()
    lattice8.project('output').rmepsilon()

    # Extract the shortest output string
    ostring3 = pynini.shortestpath(lattice3).string()
    ostring8 = pynini.shortestpath(lattice8).string()
    print(ostring3)
    print(ostring8)

    # Extract the 2 shortest unique output strings
    lattice = pynini.shortestpath(lattice3, nshortest=2, unique=True)
    ostrings = list(lattice.paths().ostrings())
    print(ostrings)

    # Approximate a full deterministic FSA from a non-deterministic
    # one using pruned determinization, which prefers shorter paths as
    # measured by path weights, then extract all rewrites. Note: the
    # state threshold is an upper bound for the deterministic FSA.
    string = pynini.accep('b') ** (5,20) | pynini.accep('a') ** (5,20)
    lattice = string @ rule3
    state_threshold = 4 * lattice.num_states() + 8
    det_lattice = pynini.determinize(lattice, nstate=state_threshold)
    ostrings = list(det_lattice.paths().ostrings())
    print(ostrings)

    # Determine whether there are ties for the single shortest path
    # while avoiding implementation-defined tie resolution. We do this
    # by applying pruned determinization with a weight threshold
    # equalt to the 1-weight of the semiring, which gives an acyclic,
    # deterministic, epsilon-free acceptor containing all optimal
    # paths, i.e. paths whose weight is equal to that of the single
    # shortest path.
    one = pynini.Weight.one(lattice.weight_type())  # 1-weight (or "free" weight) for the semiring
    det_lattice = pynini.determinize(lattice, weight=one)
    ostrings = list(det_lattice.paths().ostrings())
    there_are_ties = len(ostrings) > 1
    print(there_are_ties)

    # Test some methods from the `rewrite` module. These take an input
    # string or automaton and a rule transducer, then construct the
    # output lattice, and return either a single output string or a
    # list thereof.
    rule = pynini.cdrewrite(
        pynini.cross('b', 'a'),
        'b',
        'b',
        pynini.union('a', 'b', 'c').closure(),
    )
    string = pynini.union('a', 'b', 'c') ** (3,4)    

    # `rewrites` returns all output strings in an arbitrary order
    rewrites = rewrite.rewrites(string, rule)
    print(rewrites)

    # `top_rewrites` returns the n shortest-path output strings in an
    # arbitrary order
    rewrites = rewrite.top_rewrites(string, rule, nshortest=2)
    print(rewrites)

    # `top_rewrite` returns the shortest-path output string using
    # implementation-defined tie resolution
    top = rewrite.top_rewrite(string, rule)
    print(top)

    # `one_top_rewrite` returns the sing shortest-path output string,
    # raising an exception if there is a tie for the shortest output
    # path
    string = pynini.accep('bbb', 3) | pynini.accep('bbbb', 4)
    top = rewrite.one_top_rewrite(string, rule)
    print(top)

    # `optimal_rewrites` returns all output strings which have the
    # same weight as the single shortest path in an arbitrary order
    string = pynini.accep('bbb', 3) | pynini.accep('bbbb', 3) | pynini.accep('aa', 4)
    rewrites = rewrite.optimal_rewrites(string, rule)
    print(rewrites)

    # `matches` tests if a rule matches an input-output string pair
    # (i.e. there is a non-empty intersection between 1. the output
    # projection of the composition of string or string acceptor x
    # with the rule and 2. the string or strin acceptor y).
    matches = rewrite.matches('bbb', 'bab', rule)
    print(matches)
    return


def cascade(istring: pynini.FstLike,
            rules: Iterable[pynini.Fst]) -> pynini.Fst:
    lattice = istring
    for rule in rules:
        lattice @= rule
        assert lattice.start() != pynini.NO_STATE_ID
        lattice.project("output").rmepsilon()
    return lattice


def run_cascade():
    # If composing the rules would produce an automaton that is not
    # prohibitively large, we can simply compose the rules to create a
    # cascade. Otherwise, it is  preferable to use a loop.
    sigma_star = SPANISH_ALPHABET.closure().optimize()
    r1 = pynini.cdrewrite(
        pynini.cross('c', 's'),
        '',
        pynini.union('i', 'e'),
        sigma_star
    )
    r2 = pynini.cdrewrite(
        pynini.cross('c', 'k'),
        '',
        '',
        sigma_star
    )

    # Cascade using composition
    istring = pynini.accep('cima') | pynini.accep('escudo')
    casc = r1 @ r2
    olattice = istring @ casc
    olattice.optimize()
    ostrings = list(olattice.paths().ostrings())
    print(ostrings)
    
    # Cascade using loop
    olattice = cascade(istring, [r1, r2])
    olattice.optimize()
    ostrings = list(olattice.paths().ostrings())
    print(ostrings)
    return


def exclude(istring: pynini.FstLike,
            rules: Iterable[pynini.Fst]) -> Optional[pynini.Fst]:
    for rule in rules:
        lattice = istring @ rule
        #print("  {}".format(list(lattice.paths().ostrings())))
        if lattice.start() == pynini.NO_STATE_ID:
            continue
        return lattice.project('output').rmepsilon()


def priority_union(mu: pynini.Fst, nu: pynini.Fst,
                   sigma_star: pynini.Fst) -> pynini.Fst:
    """Priority union of 2 relations mu and nu is like their union,
    except that mu takes precedence over nu.

    """
    nu_not_mu = (sigma_star - pynini.project(mu, 'input')) @ nu
    return mu | nu_not_mu

def run_exclusion():
    # Build transducer for irregular plurals in English (or rather a
    # subset thereof, for this examples)
    irregular = pynini.string_map(
        [
            "deer",
            "fish",
            "sheep",
            ("foot", "feet"),
            ("mouse", "mice"),
            ("child", "children"),
            ("ox", "oxen"),
            ("wife", "wives"),
            ("wolf", "wolves"),            
            ("analysis", "analyses"),
            ("nucleus", "nuclei")
        ]
    )
    v = pynini.union('a', 'e', 'i', 'o', 'u')
    c = pynini.union(
        'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n',
        'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z')

    # Rule for 'ies' plurals after consonants
    sigma_star = pynini.union(v, c).closure().optimize()
    ies_rule = sigma_star + c + pynini.cross('y', 'ies') # left context is sigma* + consonant

    # Rule for 'es' plurals after certain specific stems.
    sibilant = pynini.union('s', 'sh', 'ch', 'x', 'z')
    es_rule = sigma_star + sibilant + pynutil.insert('es') # left context is sigma* + sibilant

    # Default plural
    s_rule = sigma_star + pynutil.insert('s')

    # Apply exclusing using loop (which, as implemented, requires that
    # we loop over input strings)
    inputs = ['deer', 'child', 'church', 'battery', 'fold']
    for s in inputs:
        istring = pynini.accep(s)
        olattice = exclude(istring, [irregular, ies_rule, es_rule, s_rule])
        if olattice:
            ostrings = list(olattice.paths().ostrings())
            print(ostrings)
        else:
            print("No output for {}".format(istring.string()))

    # Apply exclusion by repeatedly applying priority union to
    # construct a single transducer
    rule = priority_union(
        irregular, # Highest priority
        priority_union(ies_rule, # 2nd highest priority
                       priority_union(es_rule, # 3rd highest priority
                                      s_rule, # Lowest priority (default)
                                      sigma_star),
                       sigma_star),
        sigma_star
    ).optimize()
    istring = pynini.union(*inputs)
    olattice = istring @ rule
    ostrings = list(olattice.paths().ostrings())
    print(ostrings)
    return


def run_spanish_g2p():
    g = SPANISH_ALPHABET
    p = SPANISH_PHONEMES

    # sigma^* for the rewrite rules must contain both graphemes and
    # phonemes
    sigma_star = pynini.union(g, p).closure().optimize()






    # First rule, a set of unconditioned, surface-true
    # generalizations, which can therefore be expressed as a single
    # rewrite rule
    r1 = pynini.cdrewrite(
        pynini.string_map(
            [
                ("ch", "tʃ"),
                ("ll", "ʝ"),
                ("qu", "k"),
                ("j", "x"),
                ("ñ", "ɲ"),
                ("v", "b"),
                ("x", "s"),
                ("y", "j"),
                ("á", "a"),
                ("é", "e"),
                ("í", "i"),
                ("ó", "o"),
                ("ú", "u"),
                ("ü", "w")
            ]
        ),
        "",
        "",
        sigma_star,
    ).optimize()

    # Delete 'h', which is normally silent (except in 'ch', which was
    # handled by r1)
    r2 = pynini.cdrewrite(
        pynutil.delete('h'),
        '',
        '',
        sigma_star
    ).optimize()

    # Pronounce 'r'. First, map intervocalic 'r' to flap.
    v = pynini.union('a', 'e', 'i', 'o', 'u')
    r3 = pynini.cdrewrite(
        pynini.cross('r', 'ɾ'),
        v,
        v,
        sigma_star
    ).optimize()

    # Map 'rr' (which is always intervocalic) to trill
    r4 = pynini.cdrewrite(
        pynini.cross('rr', 'r'),
        '',
        '',
        sigma_star
    ).optimize()

    # Pronounce 'c' and 'g' before front vowels 'i' and 'e'
    front = pynini.union('i', 'e')
    r5 = pynini.cdrewrite(
        pynini.string_map(
            [
                ('c', 's'),
                ('g', 'x')
            ]
        ),
        '',
        front,
        sigma_star
    ).optimize()

    # Default for 'c'
    r6 = pynini.cdrewrite(
        pynini.cross('c', 'k'),
        '',
        '',
        sigma_star
    ).optimize()

    # Cascade
    rules = r1 @ r2 @ r3 @ r4 @ r5 @ r6

    # Restrict input to graphemes and output to phonemes
    g2p = pynini.closure(g) @ rules @ pynini.closure(p)
    g2p.optimize()

    # Test a few words
    istrings = pynini.union("perro", "pero", "cima", "escudo", "gema", "escudo")
    olattice = istrings @ g2p
    ostrings = list(olattice.paths().ostrings())
    print(ostrings)
    return


def run_finnish_case_suffix():
    # Define classes of vowels
    back = pynini.union('a', 'o', 'u')
    front = pynini.union('ä', 'ö', 'y')
    neutral = pynini.union('e', 'i')
    v = pynini.union(back, front, neutral, 'A') # 'A' is an archiphonemic vowel
    c = pynini.union(
        'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm',
        'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'z'
    )
    sigma_star = pynini.union(v, c).closure()

    # Compose and jointly optimize 2 rules for harmony. First, 'A'
    # becomes 'a' when the left context is a back vowel followed by
    # any number of neutral vowels or consonants
    r1 = pynini.cdrewrite(
        pynini.cross('A', 'a'),
        back + pynini.union(neutral, c). closure(),
        '',
        sigma_star
    )
    # In other contexts, 'A' becomes 'ä'
    r2 = pynini.cdrewrite(
        pynini.cross('A', 'ä'),
        '',
        '',
        sigma_star
    )
    harmony = r1 @ r2
    harmony.optimize()
    assert rewrite.one_top_rewrite('verollA', harmony) == 'verolla'
    assert rewrite.one_top_rewrite('kesyllA', harmony) == 'kesyllä'

    def adessive(cf: str) -> str:
        """Given the citation form (nominative singular), generate the
        appropriate adessive form.
        
        """
        return rewrite.one_top_rewrite(cf + 'llA', harmony)

    assert rewrite.one_top_rewrite(adessive('vero'), harmony) == 'verolla'
    assert rewrite.one_top_rewrite(adessive('kesy'), harmony) == 'kesyllä'
    return


def run_money_tagging():
    cur_symbol = pynini.union("$", "£", "¥", "€")
    major = byte.DIGIT ** (0, ...)
    minor = byte.DIGIT ** (2, ...)
    cur_numeric = major + ("." + minor) ** (0,1)
    cur_exp = cur_symbol + cur_numeric # Currency expression

    # Define a (non-greedy) tagger
    tagger = pynini.cdrewrite(
        pynutil.insert('<cur>') + cur_exp + pynutil.insert('</cur>'),
        '',
        '',
        byte.BYTE ** (0, ...)
    ).optimize()
    istring = pynini.accep('£50')
    olattice = istring @ tagger
    ostrings = list(olattice.paths().ostrings())
    print(ostrings)
    
    # To define a greedy tagger, add a negative weight to each digit
    # matched, then compute shortest path using `one_top_rewrite`
    major = pynutil.add_weight(byte.DIGIT, -1) ** (0, ...)
    minor = pynutil.add_weight(byte.DIGIT, -1) ** (2, ...)    
    cur_numeric = major + ("." + minor) ** (0,1)
    cur_exp = cur_symbol + cur_numeric
    tagger = pynini.cdrewrite(
        pynutil.insert('<cur>') + cur_exp + pynutil.insert('</cur>'),
        '',
        '',
        byte.BYTE ** (0, ...)
    ).optimize()
    ostring = rewrite.one_top_rewrite(istring, tagger)
    print(ostring)
    return


def main():
    run_basics()
    run_cascade()
    run_exclusion()
    run_spanish_g2p()
    run_finnish_case_suffix()
    run_money_tagging()
    return


if __name__ == "__main__":
    main()
    
