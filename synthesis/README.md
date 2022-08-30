# Generating and solving SMT constraint rules given input DFA

This folder contains python script that uses Z3py binding to construct and solve the SMT constraints describing the DFA state transitions.

For historical reasons, we have multiple variants of the script that generates slightly different contraint tree and have different performance. Please use the `_twb2` variant for the best performance. However, note that it only supports a fixed set of 6 arithmetic operations.
