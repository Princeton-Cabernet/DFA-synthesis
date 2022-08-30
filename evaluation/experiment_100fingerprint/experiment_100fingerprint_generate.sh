#!/bin/bash

mkdir -p experiment_100fingerprint/
mkdir -p experiment_100fingerprint/input/
FPDIR=examples/fingerprint/

echo "Prepare 1xLEN"
for LEN in `seq 4 2 24`; do
	echo "1x$LEN"
	pushd $FPDIR
	    python3 generate.py --length=$LEN -N=100; cat size_0.txt
	popd

	OUTDIR=experiment_100fingerprint/input/1x$LEN/
	mkdir -p $OUTDIR
	for I in `seq 0 99`; do
		cp $FPDIR/size_$I.json $OUTDIR/fingerprint.1x$LEN.$I.json
	done
done

echo "Prepare 2xLEN"
for LEN in `seq 4 2 24`; do
	echo "2x$LEN"
	pushd $FPDIR
		python3 generate.py --length=$LEN -N=200; cat size_[0-1].txt
	popd

	OUTDIR=experiment_100fingerprint/input/2x$LEN/
	mkdir -p $OUTDIR
	for I in `seq 0 99`; do
		echo -n '.'
		IN0=$(expr $I \* 2)
		IN1=$(expr $IN0 + 1)
		python3 compose_simultaneous_trie.py $FPDIR/size_$IN0.txt $FPDIR/size_$IN1.txt > $OUTDIR/fingerprint.2x$LEN.$I.json
	done
done

echo "Prepare 3xLEN"
for LEN in `seq 4 2 16`; do
	echo "3x$LEN"
	pushd $FPDIR
		python3 generate.py --length=$LEN -N=300; cat size_[0-2].txt
	popd

	OUTDIR=experiment_100fingerprint/input/3x$LEN/
	mkdir -p $OUTDIR
	for I in `seq 0 99`; do
		echo -n '.'
		IN0=$(expr $I \* 2)
		IN1=$(expr $IN0 + 1)
		IN2=$(expr $IN0 + 2)
		python3 compose_simultaneous_trie.py $FPDIR/size_$IN0.txt $FPDIR/size_$IN1.txt $FPDIR/size_$IN2.txt > $OUTDIR/fingerprint.3x$LEN.$I.json
	done
done

echo "Prepare 4xLEN"
for LEN in `seq 4 2 16`; do
	echo "4x$LEN"
	pushd $FPDIR
		python3 generate.py --length=$LEN -N=400; cat size_[0-3].txt
	popd

	OUTDIR=experiment_100fingerprint/input/4x$LEN/
	mkdir -p $OUTDIR
	for I in `seq 0 99`; do
		echo -n '.'
		IN0=$(expr $I \* 2)
		IN1=$(expr $IN0 + 1)
		IN2=$(expr $IN0 + 2)
		IN3=$(expr $IN0 + 3)
		python3 compose_simultaneous_trie.py $FPDIR/size_$IN0.txt $FPDIR/size_$IN1.txt $FPDIR/size_$IN2.txt $FPDIR/size_$IN3.txt > $OUTDIR/fingerprint.4x$LEN.$I.json
	done
done

echo "All done!"