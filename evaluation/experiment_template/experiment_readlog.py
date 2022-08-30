import json
import os

def readlog(fn): #read 3rd line
    if not os.path.isfile(fn):
        return "NONEXISTENT"
    with open(fn,'r') as f:
        lines=[l.strip() for l in f.readlines()]
        if len(lines) < 3: return "EMPTY"
        check3 = lines[3] if len(lines) == 4 else "True"
        lastline = "{:.2f}".format(float(lines[2]))

        if lines[0] == "True":
            if lines[1] == "True" and check3 == "True":
                return lastline.strip()
            else:
                return "ERROR"
        else:
            return "unsat_" + lastline.strip()

if __name__ == '__main__':
#    files = ["zoom_simple.json", "mobiledevice.json", "tcp_open.json", "simple.json"] \
#            + ["fingerprint_%s.json" % suf for suf in ["16x1", "8x3", "10x3", "12x3", "8x4", "10x4", "12x4"] ] \
#            + ["s%d.json" % i for i in range(2,5)] + ["p%d.json" % i for i in range(2,5)]

    files =  ["zoom_simple.json", "tcp_open.json"]
    params = ["Assignment","Arithmetic","TwoCond","TwoSlot","FourBranch"]

    for trial in range(11,12):
        directory = f"/media/data/mengying/P4DFA/eval_correct_{trial}"
        print('input\t'+'\t '.join(params))
        for f in files:
            line=[readlog(f"{directory}/result_{p}_{f}.log") for p in params]
            print(f+'\t'+'\t'.join(line))
        print()
        print()

    for trial in range(11, 12):
        directory = f"/media/data/mengying/P4DFA/eval_correct_{trial}"
        for f in files:
            print("======================" + f + "======================")
            for p in params:
                print(p)
                fn = f"{directory}/error_{p}_{f}.log"
                if not os.path.isfile(fn):
                    print("NONEXISTENT")
                with open(fn,'r') as fh:
                    lines = fh.readlines()
                    lines[-1] = lines[-1].strip()
                    for l in lines:
                        print("\t" + l)
            print()
