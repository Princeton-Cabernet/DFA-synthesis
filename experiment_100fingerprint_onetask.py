import itertools
import argparse
import sys
import os

params = {"Assignment" : {"two_cond": False, "two_slot": False, "four_branch": False, #"num_regact": 3,
                                "arith_bin": False, "num_arith": 6, "bitvecsize": 8, "timeout": 3600, "probe": False, "main_fixed": True},
              "Arithmetic" : {"two_cond": False, "two_slot": False, "four_branch": False, "num_regact": 3,
                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 3600, "probe": False, "main_fixed": True},
              "TwoCond" : {"two_cond": True, "two_slot": False, "four_branch": False, #"num_regact": 3,
                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 3600, "probe": False, "main_fixed": True}, 
              "TwoSlot" : {"two_cond": True, "two_slot": True, "four_branch": False, #"num_regact": 3,
                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 3600, "probe": False, "main_fixed": True},
              "FourBranch" : {"two_cond": True, "two_slot": True, "four_branch": True, #"num_regact": 3,
                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 3600, "probe": False, "main_fixed": True}}
       # "num_split_nodes": 1
       # removed from config, since 1 is default for some but unsupported by others
params = {
	f"{k}{nra}" : ( dict(v, num_regact=nra) ) 
	for nra in (2,3,4)
	for k,v in params.items()
}

parser = argparse.ArgumentParser(description='Generate running script for one experiment, given a particular input FP length.')
parser.add_argument('CLEN',type=str,
		choices=[f'{i}x{l}' for i in (1,2) for l in range(2,25,2)]+[f'{i}x{l}' for i in (3,4) for l in range(2,17,2)],
		help="The Fingerprint DFA input length and composition, e.g., '3x10'.")
parser.add_argument('PARAM',type=str,
		choices=params.keys(),
		help="The template config for the list of options passed to the DFA synthesis program.")
parser.add_argument('MAIN_PROGRAM', type=str,
		choices=['genDFA.py','tryWithBools2.py','tryWithBools3.py'],
		help="The main synthesizer to invoke.")
parser.add_argument('--tsp', action='store_true', 
		help="Append tsp in front of each command. (Turn on to let individual tasks be queued, turn off when submitting entire scripts as one tsp task.)")
parser.add_argument('--output_dir', type=str, default='experiment_100fingerprint/results/',
		help="Root output directory for saving results.")
parser.add_argument('-N','--N', type=int, default=100,
		help="Number of inputs to run, default is 100.")
parser.add_argument('--trials', type=int, default=1,
		help="Number of trials to run, default is 1.")

args=parser.parse_args()


print('#!/bin/bash')
print('# Please cd to P4DFA/ before running this script. This is a bash comment header.')
for trial in range(args.trials):
	DIR=f"{args.output_dir}/{args.CLEN}_trial{trial}/"
	if os.path.exists(DIR):
		sys.stderr.write(f"ERROR: Output folder already exists. \n {DIR}  \n\n There is risk of overwriting existing experiment data. Please move the existing data away or delete them manually.\n")
		sys.exit(-1)

	print(f"""
if [ -d "{DIR}" ]; then
    echo ERROR: Output folder already exists. {DIR}
    echo There is risk of overwriting existing experiment data. Please move the existing data away or delete them manually.
    echo Stopping this run.
    exit 1
fi
	""")
	print(f'mkdir -p {DIR}')

	for i in range(args.N):
		param=params[args.PARAM]
		args_strs = [(f"--{arg}={val}" if type(val)!= bool else (f"--{arg}" if val else "")) for arg,val in param.items()]
		all_args = ' '.join(args_strs)

		file=f"fingerprint.{args.CLEN}.{i}"

		input_file = f"experiment_100fingerprint/input/{args.CLEN}/{file}.json"
		
		param_name = args.PARAM
		jsonpath = f"{DIR}/model_{param_name}_{file}.json"
		output = f"{DIR}/result_{param_name}_{file}.log"
		error = f"{DIR}/error_{param_name}_{file}.log"

		cli=f'python3 {args.MAIN_PROGRAM} {all_args} {input_file} ' +\
			f' --jsonpath {jsonpath} > {output} 2> {error} '

		if args.tsp:
			cli='tsp bash -c "' + cli + '"'
		else:
			cli="time "+cli
		print(f"echo trial={trial} i={i}, {param_name} {file}")
		print(cli)
