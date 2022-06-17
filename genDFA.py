from z3 import *
import json
import time
import math
import itertools
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

def access_int(model, val):
    return model[val].as_long() if (model[val] != None) else None

def access_bool(model, val):
    return bool(model[val]) if (model[val] != None) else True


class Node:
    def __init__(self, leaf, height, name, data):
        self.leaf = leaf
        self.height = height
        self.name = name
        self.data = data
        self.left = None
        self.right = None

class BoolEnum:
    def __init__(self, prefix, names):
        num_leaves = len(names)
        if num_leaves == 0: 
            raise Exception("[BoolEnum] The list of vals should be nonempty.")
        tree_height = math.ceil(math.log2(num_leaves))
        self.prefix = prefix
        self.root = self.produce_node(0)

        q = []
        leaves = []
        q.append(self.root)
        while(len(q) + len(leaves) < num_leaves):
            parent = q.pop(-1)
            curr_height = parent.height + 1
            left_child = self.produce_node(curr_height)
            right_child = self.produce_node(curr_height)
            if curr_height < tree_height: 
                q.extend([right_child, left_child])
            else:
                leaves.extend([left_child, right_child])
            parent.left = left_child
            parent.right = right_child

        self.leaves = leaves + q
        for i, node in enumerate(self.leaves):
            node.leaf = True
            node.name = names[i]

    def produce_node(self, curr_height):
        node_name = "%s_%d" % (self.prefix, curr_height)
        node_data = None
        return Node(False, curr_height, node_name, node_data)

    def gen_val(self, vals):
        for i, node in enumerate(self.leaves):
            node.data = vals[i]
        return self.gen_val_helper(self.root)
    
    def gen_val_helper(self, root):
        if root.leaf:
            return root.data
        else:
            return If(Bool(root.name), 
                      self.gen_val_helper(root.left),
                      self.gen_val_helper(root.right))

    def to_string(self, model):
        return self.to_string_helper(self.root, model)

    def to_string_helper(self, root, model):
        if root.leaf:
            return root.name
        else:
            if access_bool(model, Bool(root.name)):
                return self.to_string_helper(root.left, model)
            else:
                return self.to_string_helper(root.right, model)

    def get_path(self, name):
        search, path = self.gen_path_helper(self.root, name)
        if search:
            return And(path)
        else:
            raise Exception("[BoolEnum] Name not existing.")

    def gen_path_helper(self, root, name):
        if root.leaf:
            return root.name == name, []
        left_search, left_path = self.gen_path_helper(root.left, name)
        right_search, right_path  = self.gen_path_helper(root.right, name)
        if left_search: 
            left_path.append(Bool(root.name))
            return left_search, left_path
        else: 
            right_path.append(Not(Bool(root.name)))
            return right_search, right_path
class Pred:
    def __init__(self, regact_id, pred_id, arith_bin, two_slot, bitvecsize):
        self.regact_id = regact_id
        self.pred_id = pred_id
        self.arith_bin = arith_bin
        self.two_slot = two_slot
        self.bitvecsize = bitvecsize

        op_names = ['eq', 'ge', 'le', 'neq']
        sym_names = ["const", "s1", "s2", ]
        state_names = ["const", "s1"] + (["s2"] if two_slot else [])
        self.sym_enum = BoolEnum('pred_sym_opt_%d_%d' % (self.regact_id, self.pred_id), sym_names)
        self.state_enum = BoolEnum('pred_state_opt_%d_%d' % (self.regact_id, self.pred_id), state_names)
        self.op_enum = BoolEnum('pred_op_%d_%d' % (self.regact_id, self.pred_id), op_names)
        self.const = BitVec('pred_const_%d_%d' % (regact_id, pred_id), bitvecsize)

    def makeDFACond(self):
        constraints = []
        if not self.arith_bin:
            constraints.append(Or(self.sym_enum.get_path("const"), self.state_enum.get_path("const")))
        return constraints

    def makePredCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        sym_vals = [0, symbol_1, symbol_2]
        state_vals = [0, pre_state_1] + ( [pre_state_2] if self.two_slot else [] )
        lhs = self.sym_enum.gen_val(sym_vals) + self.state_enum.gen_val(state_vals) + self.const
        op_vals = [lhs == 0, lhs >= 0, lhs <= 0, lhs != 0]
        return self.op_enum.gen_val(op_vals)

    def toJSON(self, model):
        config = { "op": self.op_enum.to_string(model),
                   "const": access_int(model, self.const),
                   "sym_opt": self.sym_enum.to_string(model),
                   "state_opt": self.state_enum.to_string(model) }
        return config

class Arith:
    def __init__(self, regact_id, arith_id, arith_bin, num_arith, two_slot, bitvecsize):
        self.regact_id = regact_id
        self.arith_id = arith_id
        self.arith_bin = arith_bin
        self.num_arith = num_arith
        self.two_slot = two_slot
        self.bitvecsize = bitvecsize

        op_names = ['plus', 'and', 'xor', 'or', 'sub', 'subr', 'nand', 'andca', 'andcb', 'nor', 'orca', 'orcb', 'xnor']
        op_names = op_names[:num_arith]
        sym_names = ["const", "s1", "s2"]
        state_names = ["const", "s1"] + ( ["s2"] if two_slot else [] )
        self.sym_enum = BoolEnum('arith_sym_opt_%d_%d' % (self.regact_id, self.arith_id), sym_names)
        self.state_enum = BoolEnum('arith_state_opt_%d_%d' % (self.regact_id, self.arith_id), state_names)
        self.op_enum = BoolEnum('arith_op_%d_%d' % (self.regact_id, self.arith_id), op_names)
        self.sym_const = BitVec('arith_sym_const_%d_%d'% (regact_id, arith_id), bitvecsize)
        self.state_const = BitVec('arith_state_const_%d_%d'% (regact_id, arith_id), bitvecsize)

    def makeDFACond(self):
        constraints = []
        if not self.arith_bin:
            constraints.append(And(Or(And(self.sym_enum.get_path("const"), self.sym_const == 0), 
                                      And(self.state_enum.get_path("const"), self.state_const == 0)),
                               self.op_enum.get_path("plus")))
        return constraints

    def makeArithCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        sym_vals = [0, symbol_1, symbol_2]
        state_vals = [0, pre_state_1] + ( [pre_state_2] if self.two_slot else [] )
        sym_val = self.sym_enum.gen_val(sym_vals)
        state_val = self.state_enum.gen_val(state_vals) 
        op_vals = [sym_val + state_val, sym_val & state_val, sym_val ^ state_val, sym_val | state_val,
                   sym_val - state_val, state_val - sym_val,
                   ~ (sym_val & state_val), (~ sym_val) & state_val, sym_val & (~ state_val),
                   ~ (sym_val | state_val), (~ sym_val) | state_val, sym_val | (~ state_val),
                   ~ (sym_val ^ state_val)]
        op_vals = op_vals[:self.num_arith]
        return self.op_enum.gen_val(op_vals)

    def toJSON(self, model):
        config = { "op": self.op_enum.to_string(model),
                   "sym_opt": self.sym_enum.to_string(model),
                   "sym_const": access_int(model, self.sym_const),
                   "state_opt": self.state_enum.to_string(model),
                   "state_const": access_int(model, self.state_const) }
        return config


class RegAct:
    def __init__(self, regact_id, arith_bin, num_arith, two_cond, two_slot, four_branch, bitvecsize):
        self.regact_id = regact_id
        self.arith_bin = arith_bin
        self.num_arith = num_arith
        self.two_cond = two_cond
        self.two_slot = two_slot
        self.four_branch = four_branch
        self.bitvecsize = bitvecsize
        self.num_pred = 2 if two_cond else 1
        self.num_arith = 4 if two_slot else 2
        self.num_logical_op = 2 if four_branch else 1
        self.preds = [Pred(regact_id, i, arith_bin, two_slot, bitvecsize) for i in range(self.num_pred)]
        self.ariths = [Arith(regact_id, i, arith_bin, num_arith, two_slot, bitvecsize) for i in range(self.num_arith)]

        op_names = ['left'] + (['and', 'or'] if two_cond else []) + (['right'] if four_branch else [])
        self.op_enums = [BoolEnum('logic_op_%d_%d' % (self.regact_id, i), op_names) for i in range(self.num_logical_op)]
        self.state_1_is_main = Bool("state_1_is_main_%d" % regact_id)
    
    def makeDFACond(self):
        constraints = []
        for p in self.preds:
            constraints.extend(p.makeDFACond())
        for a in self.ariths:
            constraints.extend(a.makeDFACond())
        if not self.two_slot:
            constraints.append(self.state_1_is_main)
        return constraints

    def makeTransitionCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2, post_state_1, post_state_2, post_state_1_is_main, trans_name):
        constraints = []

        pred_vars = [Bool('pred_val_%d_%d_%s' % (self.regact_id, i, trans_name)) for i in range(self.num_pred)]
        pred_vals= [p.makePredCond(pre_state_1, pre_state_2, symbol_1, symbol_2) for p in self.preds]
        for var, val in zip(pred_vars, pred_vals):
            constraints.append(var == val)

        logic_vars = [Bool('logic_val_%d_%d_%s' % (self.regact_id, i, trans_name)) for i in range(self.num_logical_op)]
        op_vals = [pred_vars[0]] + \
                  ( [And(pred_vars[0], pred_vars[1]), Or(pred_vars[0], pred_vars[1])] if self.two_cond else [] ) + \
                  ( [pred_vars[1]] if self.four_branch else [] )
        for var, op_enum in zip(logic_vars, self.op_enums):
            constraints.append(var == op_enum.gen_val(op_vals))

        arith_vars = [BitVec('arith_val_%d_%d_%s' % (self.regact_id, i, trans_name), self.bitvecsize) for i in range(self.num_arith)]
        arith_vals= [a.makeArithCond(pre_state_1, pre_state_2, symbol_1, symbol_2) for a in self.ariths]
        for var, val in zip(arith_vars, arith_vals):
            constraints.append(var == val)

        logic_constraints = []
        if self.two_slot:
            if self.four_branch:
                logic_constraints.append(post_state_1 == If(logic_vars[0], arith_vars[0], arith_vars[2]))
                logic_constraints.append(post_state_2 == If(logic_vars[1], arith_vars[1], arith_vars[3]))
            else:
                logic_constraints.append(post_state_1 == If(logic_vars[0], arith_vars[0], arith_vars[2]))
                logic_constraints.append(post_state_2 == If(logic_vars[0], arith_vars[1], arith_vars[3]))
            constraints.append(self.state_1_is_main == post_state_1_is_main)
        else:
            logic_constraints.append(post_state_1 == If(logic_vars[0], arith_vars[0], arith_vars[1]))
        return constraints, And(logic_constraints)

    def toJSON(self, model):
        config = { "logic_ops": [op_enum.to_string(model) for op_enum in self.op_enums],
                   "preds" : [p.toJSON(model) for p in self.preds], 
                   "ariths" : [a.toJSON(model) for a in self.ariths],
                   "state_1_is_main" : bool(model[self.state_1_is_main]) }
        return config

def toJSON(model, symbols_1, symbols_2, regact_id, states_1, states_2, states_1_is_main, regacts, two_slot, bitvecsize):
    config = {}
    config["bitvecsize"] = bitvecsize
    config["symbols_1"] = { sym : access_int(model, val) for sym, val in symbols_1.items() }
    config["symbols_2"] = { sym : access_int(model, val) for sym, val in symbols_2.items() }
    config["regact_id"] = { sym : int(val.to_string(model)) for sym, val in regact_id.items()}
    config["states_1"] = { state : [access_int(model, val)] for state, val in states_1.items() }
    if two_slot:
        config["states_2"] = { state : [access_int(model, val)] for state, val in states_2.items() }
        config["states_1_is_main"] = { state : bool(model[val]) for state, val in states_1_is_main.items() }
    config["regacts"] = [r.toJSON(model) for r in regacts]
    return config

def orderBySymbol(transitions):
    result = {}
    for transition in transitions:
        if transition[1] in result:
            result[transition[1]].append(transition)
        else:
            result[transition[1]] = [transition]
    return sorted(result.values(), key = lambda l: len(set([transition[2] for transition in l])))

def orderByState(transitions):
    result = {}
    for transition in transitions:
        if transition[2] in result:
            result[transition[2]].append(transition)
        else:
            result[transition[2]] = [transition]
    return sorted(result.values(), key = len)

def createDFA(input, arith_bin, num_arith, two_cond, two_slot, four_branch, num_regact, bitvecsize, timeout, probe):
    states, symbols, transitions = input["states"], input["sigma"], input["transitions"]

    # constraints
    constraints = []

    # per RegAct
    regacts = [RegAct(i, arith_bin, num_arith, two_cond, two_slot, four_branch, bitvecsize) for i in range(num_regact)]
    for regact in regacts:
        constraints.extend(regact.makeDFACond())

    # per symbol
    symbols_1 = {}
    symbols_2 = {}
    regact_id = {}
    regact_names = [str(i) for i in range(num_regact)]

    for symbol in symbols:
        symbols_1[symbol] = BitVec("sym_1_%s" % symbol, bitvecsize)
        symbols_2[symbol] = BitVec("sym_2_%s" % symbol, bitvecsize)
        regact_id[symbol] = BoolEnum("regact_%s" % symbol, regact_names)

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

    set_param("parallel.enable", True)
    s = Then('simplify', 'solve-eqs', 'reduce-bv-size', 'max-bv-sharing', 'bit-blast', 'qffd', 'sat').solver()  
    s.set("timeout", timeout * 1000)
    s.add(And(constraints))
    if probe: ps = {opt: Probe(opt) for opt in probes()}
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

            logic_constraints = []
            for rid in range(num_regact):
                constr, logic_constr = regacts[rid].makeTransitionCond(
                    pre_state_1, pre_state_2, symbol_1, symbol_2,
                    post_state_1, post_state_2, post_state_1_is_main,
                    "%s_%s_%s" % (src_state, symbol, dst_state))
                s.add(constr)
                logic_constraints.append(logic_constr)
                if probe: 
                    constraints.extend(constr)
            new_constr = regact_id[symbol].gen_val(logic_constraints)
            s.add(new_constr)
            if probe: 
                constraints.append(new_constr)

        # if (s.check() == sat):
        #     sys.stderr.write("Sat at the %d th symbol.\n" % (num_lists_solved))
        #     num_lists_solved += 1
        # else:
        #     sys.stderr.write("Unsat at the %d th symbol.\n" % (num_lists_solved))
        #     print("-1")
        #     sys.exit()

    if s.check() == sat:
        if probe: 
            for opt, p in ps.items():
                sys.stderr.write("%s: %s\n" % (opt, p(And(constraints))))
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
    parser.add_argument('--num_arith', type=int, default=6)
    parser.add_argument('--two_cond', action='store_true')
    parser.add_argument('--two_slot', action='store_true')
    parser.add_argument('--four_branch', action='store_true')
    parser.add_argument('--num_regact', type=int, default=1)
    parser.add_argument('--bitvecsize', type=int, default=8)
    parser.add_argument('--timeout', type=int, default=1800)
    parser.add_argument('--probe', action='store_true')
    args=parser.parse_args()

    # assertion when four_branch == True: two_slot == True, two_cond == True
    assert((args.two_slot and args.two_cond) if args.four_branch else True)

    input_json=json.load(open(args.input))
    createDFA(input_json, args.arith_bin, args.num_arith, args.two_cond, args.two_slot, args.four_branch, 
              args.num_regact, args.bitvecsize, args.timeout, args.probe)

# Classic cases:
# TwoTernary: {arith_bin = True, two_cond = True, two_slot = True, four_branch = True}
# TwoSlot: {arith_bin = True, two_cond = True, two_slot = True, four_branch = False}
# TwoCond: {arith_bin = True, two_cond = True, two_slot = False, four_branch = False}
# Arith: {arith_bin = True, two_cond = False, two_slot = False, four_branch = False}
# Simple: {arith_bin = False, two_cond = False, two_slot = False, four_branch = False}
