import argparse
import pynini
from pynini.lib import pynutil, rewrite, features, paradigms


""" Tests pynini using the code snippets from Gorman & Sproat (2021),
*Finite-State Text Processing*. """


def print_forms(noun: str, pd: paradigms.Paradigm) -> None:
    lattice = rewrite.rewrite_lattice(
        noun,
        pd.stems_to_forms @ pd.feature_label_rewriter
    )
    for wordform in rewrite.lattice_to_strings(lattice):
        print(wordform)
    return


def run_russian_nouns():
    # Define some features. First arg is the feature name, the others
    # are feature values.
    case = features.Feature(
        "case", "nom", "gen", "dat", "acc", "ins", "prp"
    )
    num = features.Feature("num", "sg", "pl")
    
    # Define a category, which is a combination of features
    noun = features.Category(case, num)

    # Define some feature vectors, which are valid combinations of a
    # Category and a sequence of feature specifications.
    nomsg = features.FeatureVector(noun, "case=nom", "num=sg")
    genpl = features.FeatureVector(noun, "case=gen", "num=pl")
    inspl = features.FeatureVector(noun, "case=ins", "num=pl")

    # Make acceptor for all sequences of 0 or more bytes excluding the
    # symbol for stem boundaries, typically '+'
    stem = paradigms.make_byte_star_except_boundary()

    # Define slots for paradigm for Russian nouns known as 'hard stem
    # masculine accent A'. Each slot is a pair consisting of an
    # affixation transducer and a FeatureVector.
    slots = [
        (stem, nomsg),
        (paradigms.suffix('+a', stem),
         features.FeatureVector(noun, "case=gen", "num=sg")),
        (paradigms.suffix('+u', stem),
         features.FeatureVector(noun, "case=dat", "num=sg")),
        (stem,
         features.FeatureVector(noun, "case=acc", "num=sg")),
        (paradigms.suffix('+om', stem),
         features.FeatureVector(noun, "case=ins", "num=sg")),
        (paradigms.suffix('+e', stem),
         features.FeatureVector(noun, "case=prp", "num=sg")),
        (paradigms.suffix('+y', stem),
         features.FeatureVector(noun, "case=nom", "num=pl")),
        (paradigms.suffix('+ov', stem),
         features.FeatureVector(noun, "case=gen", "num=pl")),
        (paradigms.suffix('+am', stem),
         features.FeatureVector(noun, "case=dat", "num=pl")),
        (paradigms.suffix('+y', stem),
         features.FeatureVector(noun, "case=acc", "num=pl")),
        (paradigms.suffix('+ami', stem),
         features.FeatureVector(noun, "case=ins", "num=pl")),
        (paradigms.suffix('+ax', stem),
         features.FeatureVector(noun, "case=prp", "num=pl")),
    ]

    # Construct the paradigm
    masc_accent_a = paradigms.Paradigm(
        category=noun,
        name="hard stem masculine accent A",
        slots=slots,
        lemma_feature_vector=nomsg,
        stems=["grádus", "žurnál"]
    )

    # Define another paradigm called "masculine accent B". This will
    # have the previous paradigm as a parent, so it inherits from the
    # parent any slots that it does not redefine, in this case nom+sg
    # and acc+sg. It will also be provided a rule that deaccentuates
    # vowels when constructing the wordforms.
    deacc_map = pynini.string_map(
        [
            ("á","a"), ("é","e"), ("í","i"),
            ("ó","o"), ("ú","u"), ("ý","y")
        ]
    )
    acc_v = pynini.project(deacc_map, 'input')
    deacc_rule = pynini.cdrewrite(
        deacc_map,
        '',
        noun.sigma_star + acc_v,
        noun.sigma_star   # Note that the `noun` object provides the sigma_star here.
    ).optimize()
    slots = [
        (paradigms.suffix("+á", stem), nomsg),
        (paradigms.suffix("+ú", stem),
         features.FeatureVector(noun, "case=dat", "num=sg")),
        (paradigms.suffix("+óm", stem),
         features.FeatureVector(noun, "case=ins", "num=sg")),
        (paradigms.suffix("+é", stem),
         features.FeatureVector(noun, "case=prp", "num=sg")),
        (paradigms.suffix("+ý", stem),
         features.FeatureVector(noun, "case=nom", "num=pl")),
        (paradigms.suffix("+óv", stem),
         features.FeatureVector(noun, "case=gen", "num=pl")),
        (paradigms.suffix("+ám", stem),
         features.FeatureVector(noun, "case=dat", "num=pl")),
        (paradigms.suffix("+ý", stem),
         features.FeatureVector(noun, "case=acc", "num=pl")),
        (paradigms.suffix("+ámi", stem),
         features.FeatureVector(noun, "case=ins", "num=pl")),
        (paradigms.suffix("+áx", stem),
         features.FeatureVector(noun, "case=prp", "num=pl")),
    ]
    masc_accent_b = paradigms.Paradigm(
        category=noun,
        name="hard stem masculine accent B",
        slots=slots,
        parent_paradigm=masc_accent_a,
        lemma_feature_vector=nomsg,
        stems=["górb", "stól"],
        rules=[deacc_rule]
    )

    # Print ouptuts for "grádus" and "stól"
    print_forms("grádus", masc_accent_a)
    print_forms("stól", masc_accent_b)
    return


def run_tagalog_infixation():
    """ Infixation of verbs based on actor focus. """
    
    # Define verb focus feature (including only actor focus or none --
    # note that there are several other types of focus in Tagalog)
    focus = features.Feature("focus", "none", "actor")
    verb = features.Category(focus)
    none = features.FeatureVector(verb, "focus=none")

    # Define vowels, consonants, stem
    v = pynini.union("a", "e", "i", "o", "u")
    c = pynini.union(
        "b", "d", "f", "g", "h", "k", "l", "ly", "k", "m", "n",
        "ng", "ny", "p", "r", "s", "t", "ts", "w", "y", "x"
    )
    stem = paradigms.make_byte_star_except_boundary()

    # Define um-infixation as stem-form rule
    um = pynini.union(
        c.plus + pynutil.insert("+um+") + v + stem,
        pynutil.insert("um+") + v + stem
    )
    slots = [
        (stem, none),
        (um, features.FeatureVector(verb, "focus=actor")),
    ]
    tagalog = paradigms.Paradigm(
        category=verb,
        slots=slots,
        lemma_feature_vector=none,
        stems=["bilang", "ibig", "lipad", "kopya", "punta"]
    )
    print_forms("bilang", tagalog)
    print_forms("ibig", tagalog)
    return


def run_yowlumne_aspect():
    """Verbal aspect suffixation, with concomitant reshaping of the verb
    stem.

    """
    # Construct aspect feautre, verb category, and lemma feature
    # vector
    aspect = features.Feature(
        "aspect", "root", "dubitative", "gerundial", "durative"
    )
    verb = features.Category(aspect)
    root = features.FeatureVector(verb, "aspect=root")

    # Define vowels, consonants, stem
    v = pynini.union("a", "i", "o", "u")
    c = pynini.union(
        "c", "m", "h", "l", "y", "k", "ʔ", "d", "n", "w", "t"
    )
    stem = paradigms.make_byte_star_except_boundary()

    # Define CVCC^? template for the -inay form. Basically, if the V
    # was lengthened by duplicating the vowel, we delete the extra
    # vowel; and if there are any vowels between the 2 final
    # consonants of the verb stem, we delete all of those too.
    cvcc = (
        c + v + pynutil.delete(v).ques +
        c + pynutil.delete(v).star + c.ques
    ).optimize()

    # Define the CVCVVC^? template for the -ʔaa form. This requires us
    # to copy certain vowels to indicate lengthening. Generally
    # speaking, string relations that copy arbitrary unbounded
    # sequences are not rational relations, but one can simulate this
    # effect using an iterated union over the eligible segments.
    cvcvvc = pynini.Fst()
    for vowel in ["a", "i", "o", "u"]:
        cvcvvc.union(
            c + vowel + pynutil.delete(vowel).ques +
            c + pynutil.delete(vowel).star +
            pynutil.insert(vowel + vowel) + c.ques
        )
    cvcvvc.optimize()

    slots = [
        (stem, root),
        (paradigms.suffix("+al", stem),
         features.FeatureVector(verb, "aspect=dubitative")),
        (paradigms.suffix("+inay", stem @ cvcc),
         features.FeatureVector(verb, "aspect=gerundial")),
        (paradigms.suffix("+ʔaa", stem @ cvcvvc),
         features.FeatureVector(verb, "aspect=durative")),
    ]
    yowlumne = paradigms.Paradigm(
        category=verb,
        slots=slots,
        lemma_feature_vector=root,
        stems=["caw", "cuum", "hoyoo", "diiyl", "ʔilk", "hiwiit"]
    )
    print_forms("caw", yowlumne)
    print_forms("ʔilk", yowlumne)    
    return
    

def main():
    run_russian_nouns()
    run_tagalog_infixation()
    run_yowlumne_aspect()
    return


if __name__ == "__main__":
    main()
    
