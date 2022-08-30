import json
import sys
import collections,itertools

from verify import verify_dfa

def compose_names(tuple_s_names):
	return '_'.join(tuple_s_names)

if len(sys.argv)<3:
	print(f"Usage: {sys.argv[0]} dfa.json MAX_NUM_STEPS")
	sys.exit(-1)

file=sys.argv[1]
max_num_steps=int(sys.argv[2])

d=json.load(open(file,'r'))
verify_dfa(d)
assert(max_num_steps>1)

dict_transitions={
	(olds,sig):news
	for (olds,sig,news) in d['transitions']
} 

multistep_transitions=[
	list(itertools.product(*[d['sigma'] for i in range(num_steps)]))
	for num_steps in range(1,max_num_steps+1)
]

new_dfa={
	"states":d['states'],
	"sigma": [compose_names(tup) for l in multistep_transitions for tup in l],
	"transitions": [],
	"initial":d['initial'],
}
if 'accepting' in d:
	new_dfa['accepting']=d['accepting']

for old_s in d['states']:
	for l in multistep_transitions:
		for tup in l:
			ptr_s=old_s
			for sigma in tup:
				ptr_s=dict_transitions[(ptr_s,sigma)]
			new_dfa['transitions'].append((old_s,compose_names(tup),ptr_s))		

print(json.dumps(new_dfa))