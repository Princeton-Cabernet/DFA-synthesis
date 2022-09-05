"DFA synthesis for data plane. © Princeton University. License: AGPLv3"

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
	verify_dfa(d, require_rejecting=True)

product_state=list(itertools.product(*[d['states'] for d in dfas]))
union_sigma=set().union(*[d['sigma'] for d in dfas])

initial_list=[d['initial'] for d in dfas]

dicts_transitions=[
	collections.defaultdict(
		lambda:d['rejecting'][0],
		{
			(olds,sig):news
			for (olds,sig,news) in d['transitions']
		} 
	)
	for d in dfas
]

transitions=[
	(
		state_tup, sig, 
		[dt[(state, sig)] for (state,dt) in zip(state_tup, dicts_transitions)]
	) for state_tup in product_state for sig in union_sigma]

new_dfa={
	"states":[compose_names(t) for t in product_state],
	"sigma": list(sorted(union_sigma)),
	"transitions":[(compose_names(olds_t),sig,compose_names(news_t)) 
		for olds_t,sig,news_t in transitions],
	"initial": compose_names(initial_list)
}
print(json.dumps(new_dfa))

