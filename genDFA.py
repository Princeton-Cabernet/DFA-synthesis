from z3 import *
import json
import time
import itertools
import collections
import argparse

# for bools a,b,c return ((a & !b & !c) || (!a & b & !c) || (!a & !b & c))
def only_one_is_true(list_of_bools):
    ans = []
    for b in list_of_bools:
        clause = [b]
        for other in list_of_bools:
            if (not(b == other)):
                clause.append(Not(other))
        ans.append(And(clause))
    return Or(ans)

# input is a list of pairs (z3Bool, stringIfTrue). Returns the string corresponding to the first true
def enum_bool_to_str(model, list_of_pairs):
    for pair in list_of_pairs:
        if model.eval(pair[0]):
            return pair[1]

# constant zero
def zero(bitvecsize): return BitVecVal(0, bitvecsize)

def access(model, val):
    return model[val].as_long() if (model[val] != None) else None

class Pred:
    def __init__(self, regact_id, pred_id, arith_bin, two_slot, bitvecsize):
        self.regact_id = regact_id
        self.pred_id = pred_id
        self.arith_bin = arith_bin
        self.two_slot = two_slot
        self.bitvecsize = bitvecsize

        self.op_names = ['eq', 'ge', 'le', 'neq']
        self.sym_names = ["const", "s1", "s2", ]
        self.state_names = ["const", "s1"] + (["s2"] if two_slot else [])

        self.op_vars = [Bool('pred_op_%s_%d_%d' % (op_name, regact_id, pred_id)) for op_name in self.op_names]
        self.op_vals = [lambda x, y : x == y, lambda x, y : x >= y, lambda x, y : x <= y, lambda x, y : x != y]
        self.sym_vars = [Bool('pred_sym_opt_%s_%d_%d' % (var_name, regact_id, pred_id)) for var_name in self.sym_names]
        self.state_vars = [Bool('pred_state_opt_%s_%d_%d' % (var_name, regact_id, pred_id)) for var_name in self.state_names]
        self.const = BitVec('pred_const_%d_%d' % (regact_id, pred_id), bitvecsize)

    def makeDFACond(self):
        constraints = []
        constraints.append(only_one_is_true(self.op_vars))
        constraints.append(only_one_is_true(self.sym_vars))
        constraints.append(only_one_is_true(self.state_vars))
        if not self.arith_bin:
            constraints.append(Or(self.sym_vars[0], self.state_vars[0]))
        return constraints

    def makePredCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        constraints = []
        sym_vals = [zero(self.bitvecsize), symbol_1, symbol_2]
        state_vals = [zero(self.bitvecsize), pre_state_1] + ([pre_state_2] if self.two_slot else [])
        for op_var, op_val in zip(self.op_vars, self.op_vals):
            for sym_var, sym_val in zip(self.sym_vars, sym_vals):
                for state_var, state_val in zip(self.state_vars, state_vals):
                    constraints.append(Implies(And(op_var, sym_var, state_var), 
                                               op_val(sym_val + state_val + self.const, zero(self.bitvecsize))))
        return constraints

    def toJSON(self, model):
        config = { "op": enum_bool_to_str(model, zip(self.op_vars, self.op_names)),
                   "const": access(model, self.const),
                   "sym_opt": enum_bool_to_str(model, zip(self.sym_vars, self.sym_names)),
                   "state_opt": enum_bool_to_str(model, zip(self.state_vars, self.state_names)) }
        return config

class Arith:
    def __init__(self, regact_id, arith_id, arith_bin, two_slot, bitvecsize):
        self.regact_id = regact_id
        self.arith_id = arith_id
        self.arith_bin = arith_bin
        self.two_slot = two_slot
        self.bitvecsize = bitvecsize

        self.op_names = ['plus', 'and', 'xor']
        self.sym_names = ["const", "s1", "s2", ]
        self.state_names = ["const", "s1"] + (["s2"] if two_slot else [])

        self.op_vars = [Bool('arith_op_%s_%d_%d' % (op_name, regact_id, arith_id)) for op_name in self.op_names]
        self.op_vals = [lambda x, y : x + y, lambda x, y : x & y, lambda x, y : x ^ y]
        self.sym_vars = [Bool('arith_sym_opt_%s_%d_%d' % (var_name, regact_id, arith_id)) for var_name in self.sym_names]
        self.state_vars = [Bool('arith_state_opt_%s_%d_%d' % (var_name, regact_id, arith_id)) for var_name in self.state_names]
        self.sym_const = BitVec('arith_sym_const_%d_%d'% (regact_id, arith_id), bitvecsize)
        self.state_const = BitVec('arith_state_const_%d_%d'% (regact_id, arith_id), bitvecsize)

    def makeDFACond(self):
        constraints = []
        constraints.append(only_one_is_true(self.op_vars))
        constraints.append(only_one_is_true(self.sym_vars))
        constraints.append(only_one_is_true(self.state_vars))
        if not self.arith_bin:
            constraints.append(And(Or(And(self.sym_vars[0], self.sym_const == zero(self.bitvecsize)), 
                                      And(self.state_vars[0], self.state_const == zero(self.bitvecsize))),
                               self.op_vars[0]))
        return constraints

    def makeArithCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2, post_state):
        constraints = []
        sym_vals = [self.sym_const, symbol_1, symbol_2]
        state_vals = [self.state_const, pre_state_1] + ([pre_state_2] if self.two_slot else [])
        for op_var, op_val in zip(self.op_vars, self.op_vals):
            for sym_var, sym_val in zip(self.sym_vars, sym_vals):
                for state_var, state_val in zip(self.state_vars, state_vals):
                    constraints.append(Implies(And(op_var, sym_var, state_var),
                                               post_state == op_val(sym_val, state_val)))
        return constraints

    def toJSON(self, model):
        config = { "op": enum_bool_to_str(model, zip(self.op_vars, self.op_names)),
                   "sym_opt": enum_bool_to_str(model, zip(self.sym_vars, self.sym_names)),
                   "sym_const": access(model, self.sym_const),
                   "state_opt": enum_bool_to_str(model, zip(self.state_vars, self.state_names)),
                   "state_const": access(model, self.state_const) }
        return config

class RegAct:
    def __init__(self, regact_id, arith_bin, two_cond, two_slot, four_branch, bitvecsize):
        self.regact_id = regact_id
        self.arith_bin = arith_bin
        self.two_cond = two_cond
        self.two_slot = two_slot
        self.four_branch = four_branch
        self.bitvecsize = bitvecsize
        self.num_pred = 2 if two_cond else 1
        self.num_arith = 4 if two_slot else 2
        self.num_logical_op = 2 if four_branch else 1
        self.preds = [Pred(regact_id, i, arith_bin, two_slot, bitvecsize) for i in range(self.num_pred)]
        self.ariths = [Arith(regact_id, i, arith_bin, two_slot, bitvecsize) for i in range(self.num_arith)]

        self.op_names = ['and', 'or', 'left'] + (['right'] if four_branch else [])
        self.op_var_lists = [[Bool("logic_op_%s_%d_%d" % (op_name, regact_id, i)) for op_name in self.op_names] for i in range(self.num_logical_op)]
        self.op_vals = [lambda x, y: And(x, y), lambda x, y: Or(x, y), lambda x, y: x] + ([lambda x, y: y] if four_branch else [])
        self.state_1_is_main = Bool("state_1_is_main_%d" % regact_id)
    
    def makeDFACond(self):
        constraints = []
        for p in self.preds:
            constraints.extend(p.makeDFACond())
        for a in self.ariths:
            constraints.extend(a.makeDFACond())
        if not self.two_cond:
            assert(len(self.op_var_lists) == 1)
            assert(len(self.op_var_lists[0]) == 3)
            op_vars = self.op_var_lists[0]
            constraints.extend([op_vars[2], Not(op_vars[0]), Not(op_vars[1])])
        else:
            constraints.extend([only_one_is_true(op_vars) for op_vars in self.op_var_lists])
        if not self.two_slot:
            constraints.append(self.state_1_is_main)
        return constraints

    def makeTransitionCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2, post_state_1, post_state_2, post_state_1_is_main, trans_name):
        pred_conds= [p.makePredCond(pre_state_1, pre_state_2, symbol_1, symbol_2) for p in self.preds]
        post_state_list = [post_state_1, post_state_2, post_state_1, post_state_2] if self.two_slot else [post_state_1, post_state_1]
        arith_conds= [a.makeArithCond(pre_state_1, pre_state_2, symbol_1, symbol_2, post_state) for a, post_state in zip(self.ariths, post_state_list)]

        constraints= []
        pred_vals = [Bool('pred_val_%d_%d_%s'.format(self.regact_id, i, trans_name)) for i in range(self.num_logical_op)]
        if self.two_cond:
            for i in range(self.num_logical_op):
                for op_vars in self.op_var_lists:
                    for op_var, op_val in zip(op_vars, self.op_vals):
                        constraints.append(Implies(op_var, pred_vals[i] == op_val(And(pred_conds[0]), And(pred_conds[1]))))
        else:
            constraints.append(pred_vals[0] == And(pred_conds[0]))

        if self.two_slot:
            if self.four_branch:
                constraints.append(Implies(pred_vals[0], And(arith_conds[0])))
                constraints.append(Implies(Not(pred_vals[0]), And(arith_conds[2])))
                constraints.append(Implies(pred_vals[1], And(arith_conds[1])))
                constraints.append(Implies(Not(pred_vals[1]), And(arith_conds[3])))
            else:
                branch_true = And(arith_conds[0] + arith_conds[1])
                branch_false = And(arith_conds[2] + arith_conds[3])
                constraints.append(Implies(pred_vals[0], branch_true))
                constraints.append(Implies(Not(pred_vals[0]), branch_false))
            constraints.append(self.state_1_is_main == post_state_1_is_main)
        else:
            constraints.append(Implies(pred_vals[0], And(arith_conds[0])))
            constraints.append(Implies(Not(pred_vals[0]), And(arith_conds[1])))
        return And(constraints)

    def toJSON(self, model):
        config = { "logic_ops": [enum_bool_to_str(model, zip(op_vars, self.op_names)) for op_vars in self.op_var_lists],
                   "preds" : [p.toJSON(model) for p in self.preds], 
                   "ariths" : [a.toJSON(model) for a in self.ariths],
                   "state_1_is_main" : bool(model[self.state_1_is_main]) }
        return config

def toJSON(model, symbols_1, symbols_2, regact_id, states_1, states_2, states_1_is_main, regacts, two_slot, bitvecsize):
    config = {}
    config["bitvecsize"] = bitvecsize
    config["symbols_1"] = { sym : access(model, val) for sym, val in symbols_1.items() }
    config["symbols_2"] = { sym : access(model, val) for sym, val in symbols_2.items() }
    config["regact_id"] = { sym[0] : sym[1] for sym, val in regact_id.items() if model[val]}
    config["states_1"] = { state : [access(model, val)] for state, val in states_1.items() }
    if two_slot:
        config["states_2"] = { state : [access(model, val)] for state, val in states_2.items() }
        config["states_1_is_main"] = { state : bool(model[val]) for state, val in states_1_is_main.items() }
    config["regacts"] = [r.toJSON(model) for r in regacts]
    return config

def orderBySymbol(transitions):
    result = {}
    for transition in transitions:
        if transition[1] in result:
            result[transition[1]].append(transition)
        else:
            result[transition[1]] = []
    return sorted(result.values(), key = lambda l: len(set([transition[2] for transition in l])))

def orderByState(transitions):
    result = {}
    for transition in transitions:
        if transition[2] in result:
            result[transition[2]].append(transition)
        else:
            result[transition[2]] = []
    return sorted(result.values(), key = len)

def createDFA(input, arith_bin, two_cond, two_slot, four_branch, num_regact, bitvecsize, timeout):
    states, symbols, transitions = input["states"], input["sigma"], input["transitions"]

    # constraints
    constraints = []

    # per RegAct
    regacts = [RegAct(i, arith_bin, two_cond, two_slot, four_branch, bitvecsize) for i in range(num_regact)]
    for regact in regacts:
        constraints.extend(regact.makeDFACond())

    # per symbol
    symbols_1 = {}
    symbols_2 = {}
    regact_id = {}

    for symbol in symbols:
        symbols_1[symbol] = BitVec("sym_1_%s" % symbol, bitvecsize)
        symbols_2[symbol] = BitVec("sym_2_%s" % symbol, bitvecsize)
        for rid in range(num_regact):
            regact_id[(symbol, rid)] = Bool("regact_%s%d" % (symbol, rid))
        constraints.append(only_one_is_true([regact_id[(symbol, i)] for i in range(num_regact)]))

    # per state
    states_1 = {}
    states_2 = {}
    states_1_is_main = {}

    for state in states:
        states_1[state] = BitVec("state_1_%s" % state, bitvecsize)
        if two_slot:
            states_2[state] = BitVec("state_2_%s" % state, bitvecsize)
            states_1_is_main[state] = Bool('state_1_is_main_%s' % state)

    for s1, s2 in itertools.product(states_1.keys(), states_1.keys()):
        if s1 != s2: 
            main_state_1 = If(states_1_is_main[s1], states_1[s1], states_2[s1]) if two_slot else states_1[s1]
            main_state_2 = If(states_1_is_main[s2], states_1[s2], states_2[s2]) if two_slot else states_1[s2]
            constraints.append(main_state_1 != main_state_2)

    s = Solver()
    s.set("timeout", timeout * 1000)
    s.add(And(constraints))
    num_lists_solved = 0
    transitions = orderBySymbol(transitions)

    for transition_list in transitions:
        #per transition
        for (src_state, symbol, dst_state) in transition_list:
            pre_state_1 = states_1[src_state]
            pre_state_2 = states_2[src_state] if two_slot else None
            symbol_1 = symbols_1[symbol]
            symbol_2 = symbols_2[symbol]
            post_state_1 = states_1[dst_state]
            post_state_2 = states_2[dst_state] if two_slot else None
            post_state_1_is_main = states_1_is_main[dst_state] if two_slot else None

            for rid in range(num_regact):
                transition_condition=regacts[rid].makeTransitionCond(
                    pre_state_1, pre_state_2, symbol_1, symbol_2,
                    post_state_1, post_state_2, post_state_1_is_main,
                    "%s_%s_%s" % (src_state, symbol, dst_state))

                s.add(Implies(regact_id[(symbol, rid)], transition_condition))


        if (s.check() == sat):
            sys.stderr.write("Sat at the %d th symbol.\n" % (num_lists_solved))
            num_lists_solved += 1
        else:
            sys.stderr.write("Unsat at the %d th symbol.\n" % (num_lists_solved))
            print("-1")
            sys.exit()

    if s.check() == sat:
        sys.stderr.write("Sat with %d regacts.\n" % num_regact)
        model = s.model()
        config = toJSON(model, symbols_1, symbols_2, regact_id, states_1, states_2,
                        states_1_is_main, regacts, two_slot, bitvecsize)
        print(json.dumps(config))
    else:
        sys.stderr.write("Unsat with %d regacts.\n" % num_regact)
        print("-1")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create DFA configurations.')
    parser.add_argument('input', type=str)
    parser.add_argument('--arith_bin', action='store_true')
    parser.add_argument('--two_cond', action='store_true')
    parser.add_argument('--two_slot', action='store_true')
    parser.add_argument('--four_branch', action='store_true')
    parser.add_argument('--num_regact', type=int, default=1)
    parser.add_argument('--bitvecsize', type=int, default=8)
    parser.add_argument('--timeout', type=int, default=1800)
    args=parser.parse_args()
    # assertion when four_branch == True: two_slot == True, two_cond == True
    assert(args.two_slot and args.two_cond if args.four_branch else True)

    input_json=json.load(open(args.input))
    createDFA(input_json, args.arith_bin, args.two_cond, args.two_slot, args.four_branch, 
              args.num_regact, args.bitvecsize, args.timeout)

# Classic cases:
# TwoTernary: {arith_bin = True, two_cond = True, two_slot = True, four_branch = True}
# TwoSlot: {arith_bin = True, two_cond = True, two_slot = True, four_branch = False}
# TwoCond: {arith_bin = True, two_cond = True, two_slot = False, four_branch = False}
# Arith: {arith_bin = True, two_cond = False, two_slot = False, four_branch = False}
# Simple: {arith_bin = False, two_cond = False, two_slot = False, four_branch = False}
