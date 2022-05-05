import json
import sys
import collections, itertools
import warnings
import re

def verify_dfa(dfa):
	"Verify that the DFA is fully specified, with all transitions defined for all states."
	states=dfa['states']
	sigma=dfa['sigma']
	transitions=dfa['transitions']
	initial=dfa['initial']
	#sanity check: no duplicate state
	if len(set(states))!=len(states):
		raise ValueError(f"Duplicate keys in State? {states}")
	if len(set(sigma))!=len(sigma):
		raise ValueError(f"Duplicate keys in Sigma? {sigma}")
	if initial not in states:
		raise ValueError(f"Unknown initial state: {initial}")
	#check character set
	for s in states:
		if not re.fullmatch(r'[A-Za-z0-9\-\_]+', s, flags=0):
			warnings.warn(f"State {s} not alphanumerical: downstream program might fail.")
	for s in sigma:
		if not re.fullmatch(r'[A-Za-z0-9\-\_]+', s, flags=0):
			warnings.warn(f"Sigma {s} not alphanumerical: downstream program might fail.")
	#check transition is completely defined
	for t in transitions:
		olds,sig,news=t
		if (olds not in states) or (news not in states):
			raise ValueError(f"Transition {t} illegal: unknown state")
		if (sig not in sigma):
			raise ValueError(f"Transition {t} illegal: unknown sigma")
	origins_count=collections.Counter([(olds,sig) for olds,sig,_ in transitions])
	for olds,sig in itertools.product(states,sigma):
		if origins_count[(olds,sig)]==0:
			raise ValueError(f"Underspecified transition: state={olds} sigma={sig} not found.")
		if origins_count[(olds,sig)]!=1:
			raise ValueError(f"Duplicate transition: state={olds} sigma={sig} has more than one outgoing edges.")
	#validated
	return True

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print(f'Usage: {sys.argv[0]} dfa.json')
		sys.exit(-1)
	dfa=json.load(open(sys.argv[1],'r'))
	if verify_dfa(dfa)==True:
		print(f'Verified: {sys.argv[1]} is a well-formed DFA.')