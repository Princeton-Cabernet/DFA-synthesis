import json

def readlog(fn): #read 3rd line
    with open(fn,'r') as f:
        lines=[l.strip() for l in f.readlines()]
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
    files = ["zoom_simple.json", "mobiledevice.json", "tcp_open.json", "simple.json", "p2.json", "p3.json", "p4.json"] + ["fingerprint_%s.json" % suf for suf in ["16x1"]]
    params = ["FourBranch"]
    param = params[0]
    num_arith_list = [1, 3, 4, 6, 13]

    directory = "/media/disk2/mengying/P4DFA/arith_plot_2"

    print('input\t'+'\t '.join([str(i) for i in num_arith_list]))
    for f in files:
        line=[readlog(f"{directory}/result_{param}_{f}_{na}.log") for na in num_arith_list]
        print(f+'\t'+'\t '.join(line))
