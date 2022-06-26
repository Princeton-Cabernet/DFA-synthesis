import itertools

if __name__ == '__main__':
#    files = ["zoom_simple.json", "mobiledevice.json", "tcp_open.json", "simple.json"] \
#            + ["fingerprint_%s.json" % suf for suf in ["16x1", "8x3", "10x3", "12x3", "8x4", "10x4", "12x4"] ] \
#            + ["s%d.json" % i for i in range(2,5)] + ["p%d.json" % i for i in range(2,5)]

    files = ["zoom_simple.json"]
    
#    params = {"SingleRegAct" : {"two_cond": False, "two_slot": False, "four_branch": False, "num_regact": 1,
#                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False, "num_split_nodes": 1},
#              "FourRegAct" : {"two_cond": False, "two_slot": False, "four_branch": False, "num_regact": 4,
#                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False, "num_split_nodes": 1},
#              "TwoCond" : {"two_cond": True, "two_slot": False, "four_branch": False, "num_regact": 4,
#                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False, "num_split_nodes": 1}, 
#              "TwoSlot" : {"two_cond": True, "two_slot": True, "four_branch": False, "num_regact": 4,
#                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False, "num_split_nodes": 1},
#              "FourBranch" : {"two_cond": True, "two_slot": True, "four_branch": True, "num_regact": 4,
#                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False, "num_split_nodes": 1},
#              "TwoCondSplitNode" : {"two_cond": True, "two_slot": False, "four_branch": False, "num_regact": 4,
#                                    "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False, "num_split_nodes": 2},
#              "TwoSlotSplitNode" : {"two_cond": True, "two_slot": True, "four_branch": False, "num_regact": 4,
#                                    "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False, "num_split_nodes": 2},
#              "FourBranchSplitNode" : {"two_cond": True, "two_slot": True, "four_branch": True, "num_regact": 4,
#                                     "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False, "num_split_nodes": 2}}

    params = {"TwoCond" : {"two_cond": True, "two_slot": False, "four_branch": False, "num_regact": 4, "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False, "num_split_nodes": 1}}

    directory = "/media/data/mengying/P4DFA/eval_seed_1"
    
    for param_name, file in itertools.product(params.keys(), files):
        param = params[param_name]
        path = "examples/%s" % file
        jsonpath = f"{directory}/model_{param_name}_{file}.json"
        args_strs = [(f"--{arg}={val}" if type(val)!= bool else (f"--{arg}" if val else "")) for arg,val in param.items()]
        output = f"{directory}/result_{param_name}_{file}.log"
        command = "tsp bash -c \"python3 genDFA.py " + path + " " + " ".join(args_strs) + f" --jsonpath={jsonpath} > " + output + "; python3 simulator.py " + path + " " + jsonpath + " >> " + output + "\""

        print(command)

