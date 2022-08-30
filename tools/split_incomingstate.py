import json
import sys
import collections,itertools

from verify import verify_dfa

if len(sys.argv)<3:
	print(f"Usage: {sys.argv[0]} dfa.json NUM_SPLIT")
	sys.exit(-1)

file=sys.argv[1]
num_split=int(sys.argv[2])

input=json.load(open(file,'r'))
verify_dfa(input)
assert(num_split>0)

split_degree_thres=2

states, symbols, transitions = input["states"], input["sigma"], input["transitions"]
# graph analysis, in_degree
in_edges=collections.defaultdict(set)
out_edges=collections.defaultdict(set)
for src,sym,dst in transitions:
    in_edges[dst].add(src)
    out_edges[src].add(dst)
is_split=lambda dst:(len(out_edges[dst])<=split_degree_thres) and (len(in_edges[dst])>1)
split_to_str_fmt=lambda s:(f'spl[{s[0]}(<-{s[1]})]' if s[1]!=None else s[0])
split_to_str=lambda s:(f'{s[0]}_{s[1]}' if s[1]!=None else s[0])
expanded_states=set()
split_nodes={}
for dst in states:
    if is_split(dst):
        sys.stderr.write(f'notice: state {dst} is split into {len(in_edges[dst])} nodes.\n')
        split_nodes[dst]=[(dst, src) for src in in_edges[dst]]
    else:
        split_nodes[dst]=[(dst, None)]
    expanded_states.update(split_nodes[dst])
def map_dst_state_to_tup(dst, src):
    if is_split(dst):
        return (dst,src)
    return (dst, None)
for src,_,dst in transitions:
    assert(map_dst_state_to_tup(dst,src) in expanded_states)

expanded_transitions=[]
for (src_state, symbol, dst_state) in transitions:
    for split_src in split_nodes[src_state]: # all split src nodes need to transition correctly
        split_dst=map_dst_state_to_tup(dst_state, src_state) #if dst is split, only one node matters
        if dst_state==src_state: #self loop
            split_dst=split_src #force self loop again, reduce in-degree of split node
        sys.stderr.write(f'adding transition: {split_to_str_fmt(split_src)} -{symbol}-> {split_to_str_fmt(split_dst)}\n')        
        expanded_transitions.append((split_src,symbol,split_dst))


new_dfa={
	"states":[split_to_str(s) for s in expanded_states],
	"sigma": symbols,
	"transitions": [(split_to_str(src),sym,split_to_str(dst)) for src,sym,dst in expanded_transitions],
	"initial":input['initial'],
}
if 'accepting' in input:
	acc=[]
	for s in input['accepting']:
		acc+=split_nodes[s]
	new_dfa['accepting']=[split_to_str(s) for s in acc]

print(json.dumps(new_dfa))
verify_dfa(new_dfa)