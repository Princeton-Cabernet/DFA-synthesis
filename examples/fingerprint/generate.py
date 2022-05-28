import json
import sys
import os
import glob
import math
import argparse

filename=os.path.join(os.path.dirname(__file__), 'reed2017codaspy_1000.txt')

parser = argparse.ArgumentParser(description='Generate RegEx and DFA json using video fingerprint chunks.')
parser.add_argument('--length', type=int, default=32, 
	help="Number of segment chunks to match before accepting.")
parser.add_argument('--num_symbols', type=int, default=16, choices=range(2,26*2+1),
	help="Number of symbols to quantize into.")
parser.add_argument('--MTU', type=int, default=1450*10,
	help="Size of a packet when splitting a segment into number of packets.")
parser.add_argument('-N', type=int, default=10,
	help="Maximum number of fingerprints to produce (using first N lines of input).")

args=parser.parse_args()
assert(3 <= args.length <= 160)
assert(args.N <= 1000)

def parse(line): 
	title,_,sizes=line.split('\t')
	sizes=[int(x) for x in sizes.split(',')]
	assert(len(sizes)>=args.length)
	return title,sizes

list_symbols=[chr(65+i) for i in range(26)]+[chr(65+32+i) for i in range(26)]
def quantize(size):
    N=args.num_symbols-1
    minsize=8000
    x=(math.log(size)-math.log(minsize))/(math.log(2e6)-math.log(minsize))*N
    if x>N: x=N
    return list_symbols[int(x)]

def num_packets(size, MTU=args.MTU):
	return size//MTU

def generate_json_sizes(symbols):
	l=len(symbols)
	states=range(-1, l+1) #use -1 for invalid, l for accept
	set_symbols=sorted(set(symbols))
	transitions=[]
	for s in states:
		if s==-1 or s==l: #special case
			transitions+=[(str(s),i,str(s)) for i in set_symbols]
		else:
			correct=symbols[s]
			transitions.append((str(s),correct,str(s+1)))
			transitions+=[(str(s),i,str(-1)) for i in set_symbols if i!=correct]
	return {
		"states" : [str(x) for x in states],
	    "sigma" : list(set_symbols),
	    "transitions" : transitions,
	    "initial" : str(0),
	    "accepting" : [str(l)]
	}

def generate_json_boundary(npkt_list):
	N=len(npkt_list)
	states=[]
	transitions=[]
	symbols=['0','1']
	initial,accept,reject=f'c{0}s{0}',f'c{N}s{0}','rej'

	for i,n in enumerate(npkt_list):
		states+=[f'c{i}s{j}' for j in range(n+1)]
		transitions+=[(f'c{i}s{j}','0',f'c{i}s{j+1}') for j in range(n)]
		transitions+=[(f'c{i}s{j}','1',reject) for j in range(n)]
		transitions+=[(f'c{i}s{n}','0',reject),(f'c{i}s{n}','1',f'c{i+1}s{0}')]
	states+=[accept,reject]
	transitions+=[(st, sym, st) for sym in symbols for st in (accept,reject)]
	return {
		"states" : states,
	    "sigma" : symbols,
	    "transitions" : transitions,
	    "initial" : initial,
	    "accepting" : [accept]
	}

#first delete all earlier files
fileList = glob.glob(os.path.join(os.path.dirname(__file__), 'size*'), recursive=False)
for filePath in fileList:
		os.remove(filePath)
fileList = glob.glob(os.path.join(os.path.dirname(__file__), 'boundary*'), recursive=False)
for filePath in fileList:
		os.remove(filePath)

with open(filename, 'r') as f:
	for i,line in enumerate(f):
		if i>=args.N: break
		_,sizes=parse(line)
		sizes=sizes[:args.length]

		symbols=[quantize(s) for s in sizes]
		with open(f'size_{i}.txt','w') as f:
			f.write(''.join(symbols)+'\n')
		json.dump(generate_json_sizes(symbols), open(f'size_{i}.json','w'))

		npkt_list=[num_packets(s) for s in sizes]
		npkt_01=['0'*np+'1' for np in npkt_list]
		with open(f'boundary_{i}.txt','w') as f:
			f.write(''.join(npkt_01)+'\n')
		json.dump(generate_json_boundary(npkt_list), open(f'boundary_{i}.json','w'))
