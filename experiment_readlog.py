import json

def readlog(fn): #read 3rd line
    with open(fn,'r') as f:
        lines = f.readlines()
        check1 = lines[0].strip()
        check2 = lines[1].strip()
        lastline = lines[2].strip()
        check3 = lines[3].strip() if len(lines) == 4 else "True"
        lastline = "{:.2f}".format(float(lastline))

        if check1 == "True":
            if check2 == "True" and check3 == "True":
                return lastline.strip()
            else:
                return "unchecked"
        else:
            return "unsat_" + lastline.strip()

if __name__ == '__main__':
#    files = ["zoom_simple.json", "mobiledevice.json", "tcp_open.json", "simple.json"] \
#            + ["fingerprint_%s.json" % suf for suf in ["16x1", "8x3", "10x3", "12x3", "8x4", "10x4", "12x4"] ] \
#            + ["s%d.json" % i for i in range(2,5)] + ["p%d.json" % i for i in range(2,5)]

    files =  ["zoom_simple.json"]
#    params = ["SingleRegAct","FourRegAct","TwoCond","TwoSlot","FourBranch","TwoCondSplitNode","TwoSlotSplitNode","FourBranchSplitNode"]

    params = ["TwoCond"]

    directory = "/media/data/mengying/P4DFA/eval_seed_1"

    print('input\t'+'\t '.join(params))
    for f in files:
        line=[readlog(f"{directory}/result_{p}_{f}.log") for p in params]
        print(f+'\t'+'\t'.join(line))
