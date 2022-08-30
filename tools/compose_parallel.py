import json
import sys
import collections,itertools

from verify import verify_dfa

def compose_names(tuple_s_names):
	return '_'.join(tuple_s_names)


if len(sys.argv)<2:
	print(f"Usage: {sys.argv[0]} dfa1.json [dfa2.json dfa3.json...]")
	sys.exit(-1)

files=sys.argv[1:]
dfas=[json.load(open(f,'r')) for f in files]
#states, sigma, transitions, initial
for d in dfas:
	verify_dfa(d)

product_state=list(itertools.product(*[d['states'] for d in dfas]))
product_sigma=list(itertools.product(*[d['sigma'] for d in dfas]))
initial_list=[d['initial'] for d in dfas]

#transitions: list([a,x,a]...), (olds,sig)->news
dicts_transitions=[
	{
		(olds,sig):news
		for (olds,sig,news) in d['transitions']
	} 
	for d in dfas
]

transition_origins=[dt.keys() for dt in dicts_transitions]
product_transition_origins=itertools.product(*transition_origins)
product_transitions={
	transition_origin: [
		dicts_transitions[i][o]
		for i,o in enumerate(transition_origin)
	]
	for transition_origin in product_transition_origins
}

product_transitions_list=[
	list(zip(*list_origin_pair_st_sig))+[tuple(list_dst_s)]
	for list_origin_pair_st_sig, list_dst_s in product_transitions.items()
]

new_dfa={
	"states":[compose_names(t) for t in product_state],
	"sigma": [compose_names(t) for t in product_sigma],
	"transitions":[(compose_names(olds_t),compose_names(sig_t),compose_names(news_t)) 
		for olds_t,sig_t,news_t in product_transitions_list],
	"initial": compose_names(initial_list)
}
print(json.dumps(new_dfa))
