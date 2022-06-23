import sys
import json
import pickle
import itertools
from genDFA import createDFA
import tryWithBools2
from simulator import simulateRegAct

if __name__ == '__main__':
    result = {}
    files = ["zoom_simple.json", "mobiledevice.json", "tcp_open.json", "simple.json"] \
            + ["fingerprint_%s.json" % suf for suf in ["16x1", "8x3", "10x3", "12x3", "8x4", "10x4", "12x4"] ] \
            + ["s%d.json" % i for i in range(2,5)] + ["p%d.json" % i for i in range(2,5)]

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

    for param_name, file in itertools.product(params.keys(), files):
        try:
            param = params[param_name]
            path = "examples/%s" % file
            sys.stderr.write("(file, params) : (%s, %s)\n" % (file, param_name))
            input_json = json.load(open(path))
            sat_res, safety_check, running_time, config = createDFA(input = input_json, **param)
            simulator_check = simulateRegAct(input_json, config, False)
            sys.stderr.write("(sat_res, safety_check, simulator_check, running_time) :\
                            (%s, %s, %s, %.3f)\n" % (sat_res, safety_check, simulator_check, running_time))
            result[(file, param_name)] = sat_res, safety_check, simulator_check, running_time, config
        except Exception as e:
            sys.stderr.write(str(e))
            result[(file, param_name)] = None, None, None, None, None
        sys.stderr.write("\n")

    with open("benchmarking_table.pickle", "wb") as f:
        pickle.dump(result, f)

    sys.stderr.write("\n")
    result = {}

    params = {"SingleRegAct" : {"two_cond": False, "two_slot": False, "four_branch": False, "num_regact": 1,
                                "arith_bin": True, "bitvecsize": 8},
              "FourRegAct" : {"two_cond": False, "two_slot": False, "four_branch": False, "num_regact": 4,
                                "arith_bin": True, "bitvecsize": 8},
              "TwoCond" : {"two_cond": True, "two_slot": False, "four_branch": False, "num_regact": 4,
                                "arith_bin": True, "bitvecsize": 8}, 
              "TwoSlot" : {"two_cond": True, "two_slot": True, "four_branch": False, "num_regact": 4,
                                "arith_bin": True, "bitvecsize": 8}}

    for param_name, file in itertools.product(params.keys(), files):
        try:
            param = params[param_name]
            path = "examples/%s" % file
            sys.stderr.write("(file, params) : (%s, %s)\n" % (file, param_name))
            input_json = json.load(open(path))
            sat_res, safety_check, running_time, config = tryWithBools2.createDFA(input = input_json, **param)
            sys.stderr.write("(sat_res, safety_check, running_time) : (%s, %s, %.3f)\n" % (sat_res, safety_check, running_time))
            result[(file, param_name)] = sat_res, safety_check, running_time, config
        except Exception as e:
            sys.stderr.write(str(e))
            result[(file, param_name)] = None, None, None, None
        sys.stderr.write("\n")

    with open("benchmarking_table_check.pickle", "wb") as f:
        pickle.dump(result, f)


