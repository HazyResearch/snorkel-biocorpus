"""

Requires

1) Convert standoff format into 1 sentence per line.
2) Apply rule-based sentence boundary detection/tokenization fixes

The main goal of this step is to ensure high-quality SBD
which often breaks in the presence of complex chemical names

"""

import re
import os
import glob
import codecs
import argparse

article_rgx = re.compile("~~_PMID_([0-9]+)_~~")

elements = "(Zr|Zn|Yb|Y|Xe|W|V|U|Tm|Tl|Ti|" + \
            "Th|Te|Tc|Tb|Ta|Sr|Sn|Sm|Si|Sg|Se|Sc|Sb|S|Ru|Rn|Rh|Rf|Re|Rb|" + \
            "Ra|Pu|Pt|Pr|Po|Pm|Pd|Pb|Pa|P|Os|O|Np|No|Ni|Ne|Nd|Nb|Na|N|Mt|" + \
            "Mo|Mn|Mg|Md|Lu|Lr|Li|La|Kr|K|Ir|In|I|Hs|Ho|Hg|Hf|He|H|Ge|Gd|" + \
            "Ga|Fr|Fm|Fe|F|Eu|Es|Er|Dy|Ds|Db|Cu|Cs|Cr|Co|Cm|Cl|Cf|Ce|Cd|" + \
            "Ca|C|Br|Bk|Bi|Bh|Be|Ba|B|Au|At|As|Ar|Am|Al|Ag|Ac)"

# force hypenation for suffix modifiers of these types
# e.g., morphine-like drugs -> morphine - like drugs
chemical_modifiers = ['abusing', 'adducted', 'allergic', 'altered', 'anesthetized', 'antagonistic',
                      'associated', 'based', 'binding', 'containing', 'controlled', 'converting',
                      'deficient', 'degrading', 'dependent', 'depleted', 'depleting', 'devoid',
                      'dose', 'drug', 'ecstasy', 'elicited', 'eluting', 'evoked', 'exposed', 'free',
                      'gated', 'induced', 'inhibited', 'injected', 'kindled', 'like', 'mediated',
                      'negative', 'nephropathy', 'positive', 'pretreated', 'primed', 'rats',
                      'receptor', 'redox', 'related', 'resistance', 'resistant', 'sensitive',
                      'sparing', 'specific', 'stained', 'stimulated', 'supplemented', 'suppressible',
                      'therapy', 'treated', 'untreated', 'lowering', 'encoded', "mice", "fortified",
                      "Induced", "Injected", "precursors", "produced", "channel", "lesioned", "response",
                      "activated","exposure","loaded","synthase"]

# sentence substitution rules
sentence_repairs = {}
sentence_repairs[re.compile("i\.m \.$")]    = "i.m."
sentence_repairs[re.compile("i\.v \.$")]    = "i.v."
sentence_repairs[re.compile("a\.c \.$")]    = "a.c."
sentence_repairs[re.compile("d\.c \.$")]    = "d.c."
sentence_repairs[re.compile("s\.c \.$")]    = "s.c."
sentence_repairs[re.compile("i\.p \.$")]    = "i.p."
sentence_repairs[re.compile("i\.v\.c \.$")] = "i.v.c."
sentence_repairs[re.compile("i\.c\.v \.$")] = "i.c.v."
sentence_repairs[re.compile("i\.c\.m \.$")] = "i.c.m."
sentence_repairs[re.compile("t\.i\.d \.$")] = "t.i.d."
sentence_repairs[re.compile("b\.i\.d \.$")] = "b.i.d."

# these fixes cause more errors than they solve
#sentence_repairs[re.compile("kg \.$")] = "kg."
#sentence_repairs[re.compile("k\.g \.$")] = "k.g."

sentence_repairs[re.compile("mol \.$")]      = "mol."
sentence_repairs[re.compile("^wt\.$")]       = "wt."
sentence_repairs[re.compile("wts \.$")]      = "wts."
sentence_repairs[re.compile("mol\.wt \.$")]  = "mol.wt."
sentence_repairs[re.compile("mol\.wts \.$")] = "mol.wts."
sentence_repairs[re.compile("approx \.$")]   = "approx."

sentence_repairs[re.compile("St \.$")]   = "St."

# word concatenation rules
word_concat = {}
word_concat[re.compile(" i\.v \. ")]         = " i.v. "
word_concat[re.compile(" i\.p \. ")]         = " i.p. "
word_concat[re.compile(" s\.c \. ")]         = " s.c. "
word_concat[re.compile(" p\.o \. ")]         = " p.o. "
word_concat[re.compile(" i\.c\.v \. ")]      = " i.c.v. "
word_concat[re.compile(" i\.c\.m \. ")]      = " i.c.m. "
word_concat[re.compile("\( \-\- \)")]        = "(--)"
word_concat[re.compile(" e\.g \. ")]         = " e.g. "
word_concat[re.compile(" i\.e \. ")]         = " i.e. "
word_concat[re.compile(" \+ \+")]            = "++"
word_concat[re.compile(" t\.i\.d \. ")]      = " t.i.d. "
word_concat[re.compile(" \+ \/ \- ")]        = " +/- "
word_concat[re.compile("year\- old")]        = "year-old"
word_concat[re.compile("\( \+\s*\/\s*\-\)")] = "(+/-)"
word_concat[re.compile("\+ \/ \-")]          = "+/-"
word_concat[re.compile("Na \+ ")]            = "Na+ "

# word expanstion rules
# TODO -- remove these when we move to a sequence model
word_expand = {}
word_expand[re.compile("[-]({})".format("|".join(chemical_modifiers)))] = lambda rgx,doc: re.sub(rgx, r" - \1", doc)
word_expand[re.compile("'s")] = lambda rgx,doc: re.sub(rgx, " 's", doc)
word_expand[re.compile("[-] and")] = lambda rgx,doc: re.sub(rgx, " - and", doc)
word_expand[re.compile("[-] or")] = lambda rgx,doc: re.sub(rgx, " - or", doc)
word_expand[re.compile("[-] ,")] = lambda rgx,doc: re.sub(rgx, " - ,", doc)
word_expand[re.compile(" non[-]")] = lambda rgx,doc: re.sub(rgx, " non - ", doc)
word_expand[re.compile(" \(([A-Za-z]+)\) ")] = lambda rgx,doc: re.sub(rgx, r" ( \1 )", doc)
word_expand[re.compile("([A-Za-z]{2,})- ")] = lambda rgx,doc: re.sub(rgx, r"\1 - ", doc)

# ion expansion rules
word_expand[re.compile("(\([0-9]*[+/-]+\)[-]*) ")] = lambda rgx,doc: re.sub(rgx, r" \1 ", doc)
word_expand[re.compile(" (\([0-9]*[+/-]+\)[-]*)([A-Za-z])")] = lambda rgx,doc: re.sub(rgx, r" \1 \2", doc)
word_expand[re.compile("^(\([0-9]*[+/-]+\)[-]*)([A-Za-z])")] = lambda rgx,doc: re.sub(rgx, r"\1 \2", doc)
word_expand[re.compile(elements + "([+-]) ")] = lambda rgx,doc: re.sub(rgx, r"\1 \2 ", doc)


def rgx_transform(l, patterns, lines):
    """

    :param l:
    :param patterns:
    :param lines:
    :return:
    """
    for rgx in patterns:
        m = rgx.search(l)
        if m:
            l = l.replace(m.group(), patterns[rgx])
            if lines:
                l += " " + lines.pop(0)
                return l
    return l

def repair(doc):
    """

    :param doc:
    :return:
    """
    lines = []
    for sent in doc:
        lines.append(" ".join(sent))

    # apply sentence repairs
    debug = False
    doc = []
    while lines:
        line = lines.pop(0).strip()
        if not line:
            continue
        t_line = rgx_transform(line, sentence_repairs, lines)
        while line != t_line:
            line = t_line
            t_line = rgx_transform(line, sentence_repairs, lines)
        doc += [t_line]

    # apply word contractions
    for i in range(len(doc)):
        for rgx in word_concat:
            m = rgx.search(doc[i])
            if m:
                doc[i] = doc[i].replace(m.group(), word_concat[rgx])

    #apply word expansion
    for i in range(len(doc)):
        for rgx in word_expand:
            doc[i] = word_expand[rgx](rgx,doc[i])

        # HACK -- ensure only 1 whitespace delimiter
        doc[i] = " ".join(doc[i].split())

    return doc


def main(args):
    """

    :param args:
    :return:
    """
    filelist = glob.glob("{}/*".format(args.inputdir)) if os.path.isdir(args.inputdir) else [args.inputdir]
    filelist = [fp for fp in filelist if not os.path.isdir(fp)]

    outpath = "{}/fixes/".format(args.outputdir)
    if not os.path.exists(outpath):
        os.mkdir(outpath)

    for fp in filelist:

        # write files with new prefix to outputdir
        outpath = ".".join(fp.split(".")[0:-1] + [args.prefix] + fp.split(".")[-1:])
        outpath = "{}/{}/{}".format(args.outputdir, args.prefix, outpath.split("/")[-1])

        with codecs.open(fp,"rU",'utf-8') as fp, codecs.open(outpath,"w",'utf-8') as op:

            doc,sentence = [],[]
            for line in fp:

                if re.search(article_rgx, line) and not doc:
                    doc += [line.strip()]

                elif re.search(article_rgx, line):
                    op.write(doc[0] + u'\n')
                    doc = repair(doc[1:])
                    for l in doc:
                        op.write(l + u'\n')
                    doc = [line.strip()]

                elif line.strip() == "":
                    doc += [sentence]
                    sentence = []

                else:
                    sentence += [line.strip()]

            if doc:
                op.write(doc[0] + u'\n')
                doc = repair(doc[1:])
                for l in doc:
                    op.write(l + u'\n')


if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-i", "--inputdir", type=str, default=None,  help="input directory or file")
    argparser.add_argument("-o", "--outputdir", type=str, default=".", help="outout directory")
    argparser.add_argument("-p", "--prefix", type=str, default="fixes", help="prefix")
    args = argparser.parse_args()
    main(args)
