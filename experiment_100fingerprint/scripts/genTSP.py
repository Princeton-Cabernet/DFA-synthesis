N=20
NewN=50
for l in '1x8,1x10,1x12,1x16,2x4,2x6,2x8,3x4,4x4'.split(','):
	print(f'echo > tasks_{l}.sh')
	for a in 'Arithmetic3,TwoCond3,TwoSlot3,FourBranch3'.split(','):
		print(f"echo 'echo     {a}'>> tasks_{l}.sh")
		print(f"python3 ../../experiment_100fingerprint_onetask.py  {l} {a} tryWithBools2.py  -N {NewN}  --tsp | tail -n {NewN-N} >> tasks_{l}.sh ")
