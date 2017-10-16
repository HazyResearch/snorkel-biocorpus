Chemical Text Tokeniser, version 1.0.1

This is a module for tokenising text that contains chemical names. It
is taken from the project Oscar3, a Named Entity Recognition system
for chemistry (http://sourceforge.net/projects/oscar3-chem/). 
The tokeniser is written in Java 5, and is not compatible with Java 1.4
or earlier.

Compilation:

If you have the source version of this module, you can build it using
Ant.

Usage:

The tokeniser can be used as a Java library; see the javadoc for more
details. Alternatively, the tool can be run from the command line.
It accepts text on standard input, and outputs a list of newline-separated
tokens on standard output. On a UNIX (etc.) system, use

java -jar chemtok-1.0.0.jar

to use the tokeniser interactively, or

java -jar chemtok-1.0.0.jar < input.txt > output.txt

for non-interactive use.

This tokeniser is almost exactly the same as the one described in:

Annotation of Chemical Named Entities
Peter Corbett, Colin Batchelor, Simone Teufel
Proceedings of BioNLP 2007

To avoid unnecessary dependencies, a small change was made with the way
the tokeniser handles constructions such as C(1)-C(9) - these changes
do not affect the F scores produced by more than 0.05%. Also, as the
corpus used was in XML, it was also possible to find the positions of
the elements corresponding to citation references (which appear as numbers
in superscripts at the end of words), and use those for further tokenisation.
This package includes code that lets you make use of the analysis of XML - 
actually analysing the XML is up to you!

Please email me if you find this tokeniser useful or incorporate it into
your software, and please cite the paper if you publish results that use
it.

Please see LICENSE.txt for license conditions. 

Version history:

1.0.0 - initial release
1.0.1 - Ooops, I included the wrong wordlist in splitSuffixes.txt. The new data
is now as described in the javadoc.

Peter Corbett, ptc24@cam.ac.uk
1 June 2007