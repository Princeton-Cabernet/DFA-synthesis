import itertools

if __name__ == '__main__':
    params = {"TwoSlot" : {"two_cond": True, "two_slot": True, "four_branch": False, "num_regact": 4,
                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 3600, "probe": False, "num_split_nodes": 1, "main_fixed": True}}
    param_name = "TwoSlot"

    len_fp_list = range(13, 19)
    num_split_node_list = [1]
    example_id = [1, 9]
    num_regact_list = [2, 3, 4]

    for len_fp, sn, eg in itertools.product(len_fp_list, num_split_node_list, example_id):
        command = []
        for num_regact in num_regact_list:
            param = params[param_name]
            param["num_split_nodes"] = sn
            param["num_regact"] = num_regact
            file = f"size_{eg}.json"
            path = f"examples/fingerprint/{len_fp}/%s" % file
            directory = f"/media/data/mengying/P4DFA/eval_sn"
            jsonpath = f"{directory}/model_{param_name}_{len_fp}_{sn}_{file}_{num_regact}.json"
            args_strs = [(f"--{arg}={val}" if type(val)!= bool else (f"--{arg}" if val else "")) for arg,val in param.items()]
            output = f"{directory}/result_{param_name}_{len_fp}_{sn}_{file}_{num_regact}.log"
            error = f"{directory}/error_{param_name}_{len_fp}_{sn}_{file}_{num_regact}.log"
            command.append("python3 genDFA.py " + path + " " + " ".join(args_strs) + \
                           f" --jsonpath={jsonpath} > " + output + " 2> " + error)

        command2 = []
        for num_regact in num_regact_list:
            file = f"size_{eg}.json"
            path = f"examples/fingerprint/{len_fp}/%s" % file
            directory = f"/media/data/mengying/P4DFA/eval_sn"
            jsonpath = f"{directory}/model_{param_name}_{len_fp}_{sn}_{file}_{num_regact}.json"
            output = f"{directory}/result_{param_name}_{len_fp}_{sn}_{file}_{num_regact}.log"
            error = f"{directory}/error_{param_name}_{len_fp}_{sn}_{file}_{num_regact}.log"
            command2.append("python3 simulator.py " + path + " " + jsonpath + " >> " + output + " 2>> " + error)

        print("tsp bash -c \" %s \"" % (" && ".join(command) + " ; " + " && ".join(command2)) )
