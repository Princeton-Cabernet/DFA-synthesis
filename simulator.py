import json
import sys
import warnings

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
    def __init__(self, op, const, sym_opt, state_opt):
        self.op = op
        self.const = const
        self.sym_opt = sym_opt
        self.state_opt = state_opt
    
    def execute(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        if self.sym_opt == "s1":
            pred_sym = symbol_1
        elif self.sym_opt == "s2":
            pred_sym = symbol_2
        elif self.sym_opt == "const":
            pred_sym = 0
        else:
            warnings.warn("Null in predicate symbol.")
            pred_sym = 0
        if self.state_opt == "s1":
            pred_state = pre_state_1
        elif self.state_opt == "s2":
            pred_state = pre_state_2
        elif self.state_opt == "const":
            pred_state = 0
        else:
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
    def __init__(self, op, sym_opt, sym_const, state_opt, state_const):
        self.op = op
        self.sym_opt = sym_opt
        self.sym_const = sym_const
        self.state_opt = state_opt
        self.state_const = state_const
    
    def execute(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        if self.sym_opt == "s1":
            arith_sym = symbol_1
        elif self.sym_opt == "s2":
            arith_sym = symbol_2
        elif self.sym_opt == "const":
            if self.sym_const != None:
                arith_sym = self.sym_const
            else:
                warnings.warn("Null in arithmetic symbol constant.")
                arith_sym = 0
        else:
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
                warnings.warn("Null in arithmetic symbol constant.")
                arith_state = 0
        else:
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
        else:
            warnings.warn("Null in arithmetic operator.")
            arith_res =  arith_sym + arith_state
        return unsign(arith_res, bitvecsize)

class RegAct:
    def __init__(self, preds, ariths, logic_ops, state_1_is_main):
        self.preds = [Pred(**p) for p in preds]
        self.ariths = [Arith(**a) for a in ariths]
        self.logic_ops = logic_ops
        self.state_1_is_main = state_1_is_main if state_1_is_main != None else True
    
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


def simulateRegAct(input, config):
    global bitvecsize
    bitvecsize = config["bitvecsize"]
    symbols_1 = access(config["symbols_1"])
    symbols_2 = access(config["symbols_2"])
    regact_id = access(config["regact_id"])
    states_1 = access(config["states_1"], [])
    
    if "states_2" in config :
        states_2 = access(config["states_2"], [])
        states_1_is_main = config["states_1_is_main"]
        back_to_state = {v : k for k in input["states"] for v in (states_1[k] if states_1_is_main[k] else states_2[k])}
    else:
        states_2 = None
        states_1_is_main = None
        back_to_state = {v : k for k in input["states"] for v in states_1[k]}

    regacts = [RegAct(**r) for r in config["regacts"]]

    for transition in input["transitions"]:
        for pre_state_1 in states_1[transition[0]]:
            for pre_state_2 in (states_2[transition[0]] if states_2 != None else [None]):
                symbol_1 = symbols_1[transition[1]]
                symbol_2 = symbols_2[transition[1]]
                post_state_1 = states_1[transition[2]]
                regact_choice = regact_id[transition[1]]
                regact = regacts[regact_choice]
                post_state_2 = states_2[transition[2]] if states_2 != None else [None]

                got_state_1, got_state_2, got_state_1_is_main = regact.execute(pre_state_1, pre_state_2, symbol_1, symbol_2)
                got_state = back_to_state[got_state_1 if got_state_1_is_main else got_state_2]

                assert(got_state == transition[2])
                assert(got_state_1 in post_state_1)
                assert(got_state_2 in post_state_2)

    print("Configuration verified for the DFA.")


def main():
    if (len(sys.argv) < 3):
        print ("please give input file and configuration")
        quit()
    with open(sys.argv[1]) as file:
        input = json.load(file)
    with open(sys.argv[2]) as file:
        config = json.load(file)
    simulateRegAct(input, config)

if __name__ == '__main__':
    main()
