# Tools for manipulating DFAs

This directory contains various tools for manipulating the input DFA json files.

### Composition

Multiple DFAs can be composed by the following methods:

- Parallel composition: all DFAs run in parallel, and they digest a tuple of symbols together.
- Sequential composition: only execute the second DFA (starting from the initial state) after the first DFA enters its accepting state. 
- Simultaneous composition: all DFAs run in parallel, sharing the same input symbol set. Digest one symbol at a time. If a symbol is not defined for a particular DFA, it transitions to the rejecting state. This is useful for matching multiple strings.
	- A trie variant uses the trie data structure to optimize the size of resulting DFA.

### Split

We can also split some complex DFA nodes (with multiple incoming edges) into multiple nodes.