import os
import sys

def analyzedir(root,files):
    results=[f for f in files if f.startswith('result')]
    print(root)
    totcnt=0
    truecnt=0
    validt=[]
    for r in results:
        content=open(os.path.join(root,r)).read().strip()
        if content=="":continue
        arr=content.split("\n")
        totcnt+=1
        if arr[0]=="True": truecnt+=1
        if arr[0]=="True" and arr[1]!="True": print('error!!! fn=',r)
        t=float(arr[2])
        if t<3600:
            validt.append(float(t))
    if len(validt)>0:
        avg=sum(validt)/len(validt)
    else:
        avg="AllTimeout"
    print(truecnt,'/',totcnt, avg)




clens='1x8,1x10,1x12,1x16,2x4,2x6,2x8,3x4,4x4'.split(',')

for clen in clens:
    for root,dirs,files in os.walk('experiment_100fingerprint/results/'):
        if clen in root:
            analyzedir(root,files)

