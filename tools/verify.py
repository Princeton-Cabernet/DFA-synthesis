"DFA synthesis for data plane. © Princeton University. License: AGPLv3"

import json
import sys
import collections, itertools
import warnings
import re

def verify_dfa(dfa, require_accepting=False, require_rejecting=False):
	"Verify that the DFA is fully specified, with all transitions defined for all states."
	"Note that if the accept state is present, it will be checked. However, missing accepting is allowed unless require_accepting=True."

	states=set(dfa['states'])
	if len(states)!=len(dfa['states']):
		raise ValueError("Duplicate states.")
	sigma=set(dfa['sigma'])
	if len(sigma)!=len(dfa['sigma']):
		raise ValueError("Duplicate sigma.")
	transitions=dfa['transitions']
	initial=dfa['initial']
	if 'accepting' in dfa:
		accepting=dfa['accepting']
		if require_accepting and len(accepting)==0:
			raise ValueError(f"The list of accepting state is empty, yet require_accepting is True.")
	else:
		accepting=[]
		if require_accepting:
			raise ValueError(f"The 'accepting' definition not found in dfa, yet require_accepting is True.")
	if 'rejecting' in dfa:
		rejecting=dfa['rejecting']
		if require_rejecting and len(rejecting)==0:
			raise ValueError(f"The list of accepting state is empty, yet require_accepting is True.")
	else:
		rejecting=[]
		if require_rejecting:
			raise ValueError(f"The 'rejecting' definition not found in dfa, yet require_rejecting is True.")
	#sanity check: no duplicate state
	if len(set(states))!=len(states):
		raise ValueError(f"Duplicate keys in State? {states}")
	if len(set(sigma))!=len(sigma):
		raise ValueError(f"Duplicate keys in Sigma? {sigma}")
	if initial not in states:
		raise ValueError(f"Unknown initial state: {initial}")
	for s in accepting:
		if s not in states:
			raise ValueError(f"Unknown accepting state: {s}")
	for s in rejecting:
		if s not in states:
			raise ValueError(f"Unknown rejecting state: {s}")

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