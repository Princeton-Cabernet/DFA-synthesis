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
    files = ["zoom_simple.json", "mobiledevice.json", "tcp_open.json", "simple.json", "p2.json", "p3.json", "p4.json"]
    
    files = ["zoom_simple.json"]

    params = ["FourBranch"]
    param = params[0]
    num_arith_list = [1, 3, 4, 6, 13]

    for trial in range(6, 11):
        directory = f"/media/disk2/mengying/P4DFA/arith_plot_{trial}"
        print('input\t'+'\t '.join([str(i) for i in num_arith_list]))
        for f in files:
            line=[readlog(f"{directory}/result_{param}_{f}_{na}.log") for na in num_arith_list]
            print(f+'\t'+'\t'.join(line))
        print()
        print()

    for trial in range(6, 11):
        directory = f"/media/disk2/mengying/P4DFA/arith_plot_{trial}"
        for f in files:
            print("======================" + f + "======================")
            for na in num_arith_list:
                print(na)
                fn = f"{directory}/error_{param}_{f}_{na}.log"
                if not os.path.isfile(fn):
                    print("NONEXISTENT")
                with open(fn,'r') as fh:
                    lines = fh.readlines()
                    lines[-1] = lines[-1].strip()
                    for l in lines:
                        print("\t" + l)
            print()
