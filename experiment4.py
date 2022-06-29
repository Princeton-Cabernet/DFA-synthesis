import itertools

if __name__ == '__main__':
    files = ["zoom_simple.json", "mobiledevice.json", "tcp_open.json", "simple.json", "p2.json", "p3.json", "p4.json"]

    files = ["simple.json"]
    
    params = {"FourBranch" : {"two_cond": True, "two_slot": True, "four_branch": True, "num_regact": 4,
                                "arith_bin": True, "num_arith": 6, "bitvecsize": 8, "timeout": 3600, "probe": False, "num_split_nodes": 1, "main_fixed": True}}

    num_arith_list = [1, 3, 4, 6, 13]
    for param_name, file, num_arith in itertools.product(params.keys(), files, num_arith_list):
        command = []
        for trial in range(6, 11):
            param = params[param_name]
            param["num_arith"] = num_arith
            path = "examples/%s" % file
            directory = f"/media/disk2/mengying/P4DFA/arith_plot_{trial}"
            jsonpath = f"{directory}/model_{param_name}_{file}_{num_arith}.json"
            args_strs = [(f"--{arg}={val}" if type(val)!= bool else (f"--{arg}" if val else "")) for arg,val in param.items()]
            output = f"{directory}/result_{param_name}_{file}_{num_arith}.log"
            error = f"{directory}/error_{param_name}_{file}_{num_arith}.log"
            command.append("python3 genDFA.py " + path + " " + " ".join(args_strs) + f" --jsonpath={jsonpath} > " + output + " 2> " + error)
        print("tsp bash -c \" %s \"" % (" && ".join(command)))

    for param_name, file, num_arith in itertools.product(params.keys(), files, num_arith_list):
        command = []
        for trial in range(6, 11):
            param = params[param_name]
            path = "examples/%s" % file
            directory = f"/media/disk2/mengying/P4DFA/arith_plot_{trial}"
            jsonpath = f"{directory}/model_{param_name}_{file}_{num_arith}.json"
            output = f"{directory}/result_{param_name}_{file}_{num_arith}.log"
            error = f"{directory}/error_{param_name}_{file}_{num_arith}.log"
            command.append("python3 simulator.py " + path + " " + jsonpath + " >> " + output + " 2>> " + error)

        print("tsp bash -c \" %s \"" % (" && ".join(command)))
