N=20
for a in 'Assignment3,Arithmetic3,TwoCond3,TwoSlot3,FourBranch3'.split(','):
    for l in '1x8,1x10,1x12,1x14,1x16,1x18,2x4,2x6,2x8,2x10,3x4,3x6,3x8,4x4,4x6,4x8'.split(','):
        print(f"python3 ../../experiment_100fingerprint_onetask.py  {l} {a} tryWithBools2.py  -N {N} > {l}.{a}.sh")
