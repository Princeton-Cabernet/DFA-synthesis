import sys
import json
import argparse
import warnings
import traceback

bitvecsize = 0

def access(dict, dft_val = 0):
    return {key: dict[key] if (dict[key] != None) else dft_val for key in dict.keys()}

def sign(val, num_bits):
    max_int = 1 << (num_bits - 1)
    bound = max_int << 1
    masked_val = val & (bound - 1)
    return masked_val if masked_val < max_int else masked_val - bound

def unsign(val, num_bits):
    bound = 1 << num_bits
    return val & (bound - 1)

class Pred:
    def __init__(self, op, const, sym_opt, state_opt, warning):
        self.op = op
        self.const = const
        self.sym_opt = sym_opt
        self.state_opt = state_opt
        self.warning = warning

    def execute(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        if self.sym_opt == "s1":
            pred_sym = symbol_1
        elif self.sym_opt == "s2":
            pred_sym = symbol_2
        elif self.sym_opt == "const":
            pred_sym = 0
        else:
            if self.warning:
                warnings.warn("Null in predicate sym.")
            pred_sym = 0
        if self.state_opt == "s1":
            pred_state = pre_state_1
        elif self.state_opt == "s2":
            pred_state = pre_state_2
        elif self.state_opt == "const":
            pred_state = 0
        else:
            if self.warning:
                warnings.warn("Null in predicate state.")
            pred_state = 0
        pred_const = 0 if self.const == None else self.const
        global bitvecsize
        pred_arg = sign(pred_state + pred_sym + pred_const, bitvecsize)
        if self.op == "eq":
            return pred_arg == 0
        elif self.op == "ge":
            return pred_arg >= 0
        elif self.op == "le":
            return pred_arg <= 0
        elif self.op == "neq":
            return pred_arg != 0
        else:
            warnings.warn("Null in predicate operator.")
            return pred_arg == 0

class Arith:
    def __init__(self, op, sym_opt, sym_const, state_opt, state_const, warning):
        self.op = op
        self.sym_opt = sym_opt
        self.sym_const = sym_const
        self.state_opt = state_opt
        self.state_const = state_const
        self.warning = warning
    
    def execute(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        if self.sym_opt == "s1":
            arith_sym = symbol_1
        elif self.sym_opt == "s2":
            arith_sym = symbol_2
        elif self.sym_opt == "const":
            if self.sym_const != None:
                arith_sym = self.sym_const
            else:
                if self.warning:
                    warnings.warn("Null in arithmetic symbol constant.")
                arith_sym = 0
        else:
            if self.warning:
                warnings.warn("Null in arithmetic symbol.")
            arith_sym = 0
        if self.state_opt == "s1":
            arith_state = pre_state_1
        elif self.state_opt == "s2":
            arith_state = pre_state_2
        elif self.state_opt == "const":
            if self.state_const != None:
                arith_state = self.state_const
            else:
                if self.warning:
                    warnings.warn("Null in arithmetic symbol constant.")
                arith_state = 0
        else:
            if self.warning:
                warnings.warn("Null in arithmetic state.")
            arith_state = 0
        if self.op == "plus":
            arith_res = arith_sym + arith_state
        elif self.op == "xor":
            arith_res =  arith_sym ^ arith_state
        elif self.op == "and":
            arith_res =  arith_sym & arith_state
        elif self.op == "or":
            arith_res =  arith_sym | arith_state
        elif self.op == "sub":
            arith_res =  arith_sym - arith_state
        elif self.op == "subr":
            arith_res = arith_state - arith_sym
        elif self.op == "nand":
            arith_res =  ~ (arith_sym & arith_state)
        elif self.op == "andca":
            arith_res =  (~ arith_sym) & arith_state
        elif self.op == "andcb":
            arith_res =  arith_sym & (~ arith_state)
        elif self.op == "nor":
            arith_res =  ~ (arith_sym | arith_state)
        elif self.op == "orca":
            arith_res =  (~ arith_sym) | arith_state
        elif self.op == "orcb":
            arith_res =  arith_sym | (~ arith_state)
        elif self.op == "xnor":
            arith_res =  ~ (arith_sym ^ arith_state)
        else:
            if self.warning:
                warnings.warn("Null in arithmetic operator.")
            arith_res =  arith_sym + arith_state
        return unsign(arith_res, bitvecsize)

class RegAct:
    def __init__(self, preds, ariths, logic_ops, state_1_is_main, warning):
        self.preds = [Pred(warning=warning, **p) for p in preds]
        self.ariths = [Arith(warning=warning, **a) for a in ariths]
        self.logic_ops = logic_ops
        self.state_1_is_main = state_1_is_main if state_1_is_main != None else True
        self.warning = warning
    
    def execute(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        pred_conds = [p.execute(pre_state_1, pre_state_2, symbol_1, symbol_2) for p in self.preds]
        arith_exprs = [a.execute(pre_state_1, pre_state_2, symbol_1, symbol_2) for a in self.ariths]
        pred_combos = []
        for i in range(len(self.logic_ops)):
            if self.logic_ops[i] == "left":
                pred_combos.append(pred_conds[0])
            elif self.logic_ops[i] == "right":
                pred_combos.append(pred_conds[1])
            elif self.logic_ops[i] == "and":
                pred_combos.append(pred_conds[0] & pred_conds[1])
            elif self.logic_ops[i] == "or":
                pred_combos.append(pred_conds[0] | pred_conds[1])
            else:
                if self.warning:
                    warnings.warn("Null in logical operator.")
                pred_combos.append(pred_conds[0])
        post_state_2 = None
        if len(self.ariths) == 4:
            if len(self.logic_ops) == 2:
                post_state_1 = arith_exprs[0] if pred_combos[0] else arith_exprs[2]
                post_state_2 = arith_exprs[1] if pred_combos[1] else arith_exprs[3]
            else:
                post_state_1 = arith_exprs[0] if pred_combos[0] else arith_exprs[2]
                post_state_2 = arith_exprs[1] if pred_combos[0] else arith_exprs[3]
        else:
            post_state_1 = arith_exprs[0] if pred_combos[0] else arith_exprs[1]
        return post_state_1, post_state_2, self.state_1_is_main

def string_to_pair(s):
    return tuple(s.rsplit('_', 1))

def simulateRegAct(input, config, warning):
    global bitvecsize
    bitvecsize = config["bitvecsize"]
    symbols_1 = access(config["symbols_1"])
    symbols_2 = access(config["symbols_2"])
    regact_id = access(config["regact_id"])
    states_1 = access(config["states_1"])
    states_1 = {string_to_pair(k) : v for k, v in states_1.items()}

    if "states_2" in config :
        states_2 = access(config["states_2"])
        states_2 = {string_to_pair(k) : v for k, v in states_2.items()}
        if "states_1_is_main" in config:
            states_1_is_main = {string_to_pair(k) : v for k, v in config["states_1_is_main"].items()}
            back_to_state = {(states_1[k] if v else states_2[k]) : k[0] for k, v in states_1_is_main.items()}
        else:
            states_1_is_main = None
            back_to_state = {v : k[0] for k, v in states_1.items()}
        states_2 = {state : [v for k, v in sorted(states_2.items(), key=lambda kv:kv[0][1]) if state == k[0]] for state in input["states"]}
    else:
        states_2 = None
        states_1_is_main = None
        back_to_state = {v : k[0] for k, v in states_1.items()}

    states_1 = {state : [v for k, v in sorted(states_1.items(), key=lambda kv:kv[0][1]) if state == k[0]] for state in input["states"]}

    for r in config["regacts"]:
        if "state_1_is_main" not in r: r["state_1_is_main"] = True
    regacts = [RegAct(warning=warning, **r) for r in config["regacts"]]
    for transition in input["transitions"]:
        if states_2 == None:
            it=zip(states_1[transition[0]], [None]*len(states_1[transition[0]]))
        else:
            it=zip(states_1[transition[0]], states_2[transition[0]])
        for (pre_state_1,pre_state_2) in it:
                symbol_1 = symbols_1[transition[1]]
                symbol_2 = symbols_2[transition[1]]
                post_state_1 = states_1[transition[2]]
                regact_choice = regact_id[transition[1]]
                regact = regacts[regact_choice]
                post_state_2 = states_2[transition[2]] if states_2 != None else [None]

                post_state_tuples = list(zip(post_state_1,post_state_2))

                got_state_1, got_state_2, got_state_1_is_main = regact.execute(pre_state_1, pre_state_2, symbol_1, symbol_2)
                try:
                    got_state = back_to_state[got_state_1 if got_state_1_is_main else got_state_2]
                except:
                    traceback.print_exc()
                    sys.stderr.write("No state\n")
                    sys.stderr.write(str(transition)+"\n")
                    sys.stderr.write(str(got_state_1)+"\n"+str(got_state_2)+"\n")
                    print(False)
                    return False
                if (got_state != transition[2]) or (got_state_1,got_state_2) not in post_state_tuples:
                    sys.stderr.write("Wrong state\n")
                    sys.stderr.write(str(transition)+"\n")
                    sys.stderr.write(str(got_state_1)+"\n"+str(got_state_2)+"\n")
                    print(False)
                    return False

    print(True)
    return True


def main():
    parser = argparse.ArgumentParser(description='Create DFA configurations.')
    parser.add_argument('input', type=str)
    parser.add_argument('config', type=str)
    parser.add_argument('--warning', action='store_true')
    args=parser.parse_args()

    try:
        input=json.load(open(args.input))
        config=json.load(open(args.config))
    except:
        sys.exit(-1)
    simulateRegAct(input, config, args.warning)

if __name__ == '__main__':
    main()
