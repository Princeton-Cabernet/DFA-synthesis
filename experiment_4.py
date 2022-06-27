import itertools

if __name__ == '__main__':
    files = ["zoom_simple.json", "mobiledevice.json", "tcp_open.json", "simple.json"] \
            + ["fingerprint_%s.json" % suf for suf in ["16x1", "8x3", "12x4"] ]

    params = {"TwoCond" : {"two_cond": True, "two_slot": False, "four_branch": False, "num_regact": 4,
                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False, "num_split_nodes": 1},
              "TwoSlot" : {"two_cond": True, "two_slot": True, "four_branch": False, "num_regact": 4,
                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False, "num_split_nodes": 1}}

    directory = "/media/data/mengying/P4DFA/arith_plot_1"

    num_arith_list = [1, 3, 4, 6, 13]
    for param_name, file, num_arith in itertools.product(params.keys(), files, num_arith_list):
        param = params[param_name]
        param["num_arith"] = num_arith
        path = "examples/%s" % file
        jsonpath = f"{directory}/model_{param_name}_{file}_{num_arith}.json"
        args_strs = [(f"--{arg}={val}" if type(val)!= bool else (f"--{arg}" if val else "")) for arg,val in param.items()]
        output = f"{directory}/result_{param_name}_{file}_{num_arith}.log"
        error = f"{directory}/error_{param_name}_{file}_{num_arith}.log"
        command = "tsp bash -c \"python3 genDFA.py " + path + " " + " ".join(args_strs) + f" --jsonpath={jsonpath} > " + output + " 2> " + error\
 +  " ; python3 simulator.py " + path + " " + jsonpath + " >> " + output + " 2>> " + error +  " \""

        print(command)
