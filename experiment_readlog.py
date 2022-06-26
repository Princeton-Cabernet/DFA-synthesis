import json

def readlog(fn): #read 3rd line
    with open(fn,'r') as f:
        lastline=f.readlines()[2]
        return lastline.strip()

if __name__ == '__main__':
    files = ["zoom_simple.json", "mobiledevice.json", "tcp_open.json", "simple.json"] \
            + ["fingerprint_%s.json" % suf for suf in ["16x1", "8x3", "10x3", "12x3", "8x4", "10x4", "12x4"] ] \
            + ["s%d.json" % i for i in range(2,5)] + ["p%d.json" % i for i in range(2,5)]
    params = ["SingleRegAct","FourRegAct","TwoCond","TwoSlot","FourBranch"]

    print('input\t'+'\t'.join(params))
    for f in files:
        line=[readlog(f"result_{p}_{f}.log") for p in params]
        print(f+'\t'+'\t'.join(line))
