import json
import sys
import collections,itertools

if len(sys.argv)<2:
	print(f"Usage: {sys.argv[0]} str1.txt [str2.txt str3.txt...]")
	sys.exit(-1)

files=sys.argv[1:]
strs=[open(f,'r').read().strip() for f in files]
# we assume input string are not prefix of each other.

maxlen=max([len(s) for s in strs])
union_chars=set().union(*[set(list(s)) for s in strs])


# States: unique prefixes
unique_prefixes=[]

for l in range(maxlen):
	prefixes=[s[:l] for s in strs if len(s)>l]
	for pr in set(prefixes):
		unique_prefixes.append(pr)
states=['rej']+['acc'+s for s in strs]+['p'+pr for pr in unique_prefixes]
# add transitions from all prefixes
transitions=[]
unique_prefixes=set(unique_prefixes)
for pr in sorted(unique_prefixes):
	for c in union_chars:
		from_state='p'+pr
		next_state='rej'
		if (pr+c) in strs:
			next_state='acc'+(pr+c)
		elif (pr+c) in unique_prefixes:
			next_state='p'+(pr+c)
		transitions.append((from_state,c,next_state))

# add self loop for accepting/rejecting states
for s in ['rej']+['acc'+s for s in strs]:
	for c in union_chars:
		transitions.append((s,c,s))

new_dfa={
	"states": states,
	"sigma": list(sorted(union_chars)),
	"transitions": transitions,
	"initial": 'p',
	"accepting": ['acc'+s for s in strs]
}
print(json.dumps(new_dfa))