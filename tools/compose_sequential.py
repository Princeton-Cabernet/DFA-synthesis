"DFA synthesis for data plane. © Princeton University. License: AGPLv3"

import json
import sys
import collections,itertools

from verify import verify_dfa

def compose_state(tuple_state):
	dfa_id,state=tuple_state
	return f'd{dfa_id}_{state}'
def compose_sigma(tuple_sigma):
	return '_'.join(tuple_sigma)

if len(sys.argv)<2:
	print(f"Usage: {sys.argv[0]} dfa1.json [dfa2.json dfa3.json...]")
	sys.exit(-1)

files=sys.argv[1:]
dfas=[json.load(open(f,'r')) for f in files]
#states, sigma, transitions, initial
for d in dfas:
	verify_dfa(d, require_accepting=True)

N=len(dfas)
states_seq=[(i, s) for s in d["states"] for i,d in enumerate(dfas)]
accepting_states=[d['accepting'] for d in dfas]
initial_states=[d['initial'] for d in dfas]
product_sigma=list(itertools.product(*[d['sigma'] for d in dfas]))

#transitions: list([a,x,a]...), (olds,sig)->news
dicts_transitions=[
	{
		(olds,sig):news
		for (olds,sig,news) in d['transitions']
	} 
	for d in dfas
]

transition_given_tuple_states={
	(i,s):{
		list_sig: dicts_transitions[i][(s,list_sig[i])]  #TODO accepting -> next init
		for list_sig in product_sigma
	}
	for (i,s) in states_seq
}
#rewrite accept state to new
transition_given_tuple_states_with_accept={
	(i,s): {
		k: ((i,v) if ((v not in accepting_states[i]) or (i+1==N)) else (i+1,initial_states[i+1])) 
		for k,v in transition_given_tuple_states[(i,s)].items()
	}
	for (i,s) in states_seq
}

transition_tuples=[
	(i_s,lsig,new_i_s) 
	for i_s in states_seq
	for lsig,new_i_s in transition_given_tuple_states_with_accept[i_s].items()	
]

new_dfa={
	"states":[compose_state(t) for t in states_seq],
	"sigma": [compose_sigma(t) for t in product_sigma],
	"transitions":[
	(compose_state(i_s), compose_sigma(lsig), compose_state(new_i_s))
	for (i_s,lsig,new_i_s) in transition_tuples],
	"initial": compose_state((0,initial_states[0])),
	"accepting": [compose_state((N-1,s)) for s in accepting_states[N-1]]
}
print(json.dumps(new_dfa))