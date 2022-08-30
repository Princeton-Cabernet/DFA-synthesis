#!/bin/bash

set -x
set -e

mkdir -p examples_splitnode/
for LEN in `seq 8 2 24`; do
	echo "LEN=$LEN"
	pushd examples/fingerprint/
	    python3 generate.py --length=$LEN ; cat size_0.txt
	popd

	cp examples/fingerprint/size_0.json examples_splitnode/"nosplit.1x$LEN.json"

	for SPLIT in `seq 2 2 8`; do
		echo "SPLIT=$SPLIT"
		python3 split_incomingstate.py examples/fingerprint/size_0.json $SPLIT  2>/dev/null> examples_splitnode/"spl$SPLIT.state_1x$LEN.json"
		python3 split_sym.py examples/fingerprint/size_0.json $SPLIT  2>/dev/null > examples_splitnode/"spl$SPLIT.sym_1x$LEN.json"
	done
done
