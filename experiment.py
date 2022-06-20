import sys
import json
import pickle
import itertools
from genDFA import createDFA
from simulator import simulateRegAct

if __name__ == '__main__':
    result = {}
    params = {"SingleRegAct" : {"two_cond": False, "two_slot": False, "four_branch": False, "num_regact": 1,
                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False},
              "FourRegAct" : {"two_cond": False, "two_slot": False, "four_branch": False, "num_regact": 4,
                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False},
              "TwoCond" : {"two_cond": True, "two_slot": False, "four_branch": False, "num_regact": 4,
                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False}, 
              "TwoSlot" : {"two_cond": True, "two_slot": True, "four_branch": False, "num_regact": 4,
                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False},
              "FourBranch" : {"two_cond": True, "two_slot": True, "four_branch": True, "num_regact": 4,
                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 1800, "probe": False}}

    files = ["simple.json", "zoom_simple.json"]

    for param_name, file in [("SingleRegAct", "simple.json"), ("SingleRegAct", "zoom_simple.json")]:
        param = params[param_name]
        path = "examples/%s" % file
        sys.stderr.write("(file, params) : (%s, %s)\n" % (file, param_name))
        input_json = json.load(open(path))
        sat_res, running_time, config = createDFA(input = input_json, **param)
        simulateRegAct(input_json, config)
        result[(file, param_name)] = sat_res, running_time

    with open("benchmarking_table.pickle", "wb") as f:
        pickle.dump(f, result)
