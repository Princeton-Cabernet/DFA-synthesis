from z3 import *
import json
import time
import math
import itertools
import argparse
import collections

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
            right_child = self.produce_node(curr_height)
            left_child = self.produce_node(curr_height)
            if curr_height < tree_height: 
                q.extend([left_child, right_child])
            else:
                leaves.extend([right_child, left_child])
            parent.left = left_child
            parent.right = right_child

        self.leaves = leaves + q
        self.leaves.reverse()
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
        sym_vals = [self.sym_const, symbol_1, symbol_2]
        state_vals = [self.state_const, pre_state_1] + ( [pre_state_2] if self.two_slot else [] )
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

    def makeTransitionCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2, trans_name):
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

        return constraints, logic_vars, arith_vars, self.state_1_is_main

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
    config["states_1"] = { pair_to_string(state) : access_int(model, val) for state, val in states_1.items() }
    if two_slot:
        config["states_2"] = { pair_to_string(state) : access_int(model, val) for state, val in states_2.items() }
        config["states_1_is_main"] = { pair_to_string(state) : bool(model[val]) for state, val in states_1_is_main.items() }
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

def pair_to_string(state_pair):
    if state_pair[1] == None:
        return  "%s_%d" % (state_pair[0], 0)
    else:
        return "%s_%d" % state_pair

def createDFA(input, arith_bin, num_arith, two_cond, two_slot, four_branch, num_regact, bitvecsize, timeout, probe, num_split_nodes, jsonpath=None):
    t0 = time.time()
    states, symbols, transitions = input["states"], input["sigma"], input["transitions"]

    # graph analysis, in_degree
    in_symbols=collections.defaultdict(set)
    out_edges=collections.defaultdict(set)
    for src,sym,dst in transitions:
        in_symbols[dst].add(sym)
        out_edges[src].add(dst)
    is_split=lambda dst:(len(out_edges[dst])<= 1) and (len(in_symbols[dst])>1)
    # split_to_str=lambda s:(f'spl[{s[0]}(<-{s[1]})]' if s[1]!=None else s[0])
    expanded_states=set()
    split_nodes={}
    for dst in states:
        if is_split(dst):
            sys.stderr.write(f'notice: state {dst} is split into {num_split_nodes} nodes.\n')
            split_nodes[dst]=[(dst, i) for i in range(num_split_nodes)]
        else:
            split_nodes[dst]=[(dst, None)]
        expanded_states.update(split_nodes[dst])
    expanded_transitions = []
    for src, sym, dst in transitions:
        if is_split(src):
            expanded_transitions.extend([[(src, i), sym, dst] for i in range(num_split_nodes)])
        else:
            expanded_transitions.append([(src,None), sym, dst])

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

    for state in expanded_states:
        states_1[state] = BitVec("state_1_%s" % pair_to_string(state), bitvecsize)
        if two_slot:
            states_2[state] = BitVec("state_2_%s" % pair_to_string(state), bitvecsize)
            states_1_is_main[state] = Bool('state_1_is_main_%s' % pair_to_string(state))

    for s1, s2 in itertools.combinations(states_1.keys(), 2):
        if s1 != s2: 
            main_state_1 = If(states_1_is_main[s1], states_1[s1], states_2[s1]) if two_slot else states_1[s1]
            main_state_2 = If(states_1_is_main[s2], states_1[s2], states_2[s2]) if two_slot else states_1[s2]
            if s1[0] != s2[0]:
                constraints.append(main_state_1 != main_state_2)

    #set_param("parallel.enable", True)
    s = Then('simplify', 'solve-eqs', 'bit-blast', 'qffd', 'sat').solver()  
    s.set("timeout", timeout * 1000)
    s.add(constraints)
    if probe: ps = {opt: Probe(opt) for opt in probes()}
    # num_lists_solved = 0
    for (src_state_split, symbol, dst_state) in expanded_transitions:
        pre_state_1 = states_1[src_state_split]
        pre_state_2 = states_2[src_state_split] if two_slot else None
        symbol_1 = symbols_1[symbol]
        symbol_2 = symbols_2[symbol]

        s1explist = []
        s2explist = []
        tuple_options = range(num_split_nodes) if is_split(dst_state) else [None]
        constr_all = []
        for rid in range(num_regact):
            constr, logic_vars, arith_vars, state_1_is_main = regacts[rid].makeTransitionCond(
                pre_state_1, pre_state_2, symbol_1, symbol_2,
                "%s_%d_%s_%s" % (src_state_split[0], 0 if src_state_split[1] == None else src_state_split[1], symbol, dst_state))
            constr_all.extend(constr)
            if two_slot:
                s1exp = If(logic_vars[0], arith_vars[0], arith_vars[2])
                if four_branch:
                    s2exp = If(logic_vars[1], arith_vars[1], arith_vars[3])
                else:
                    s2exp = If(logic_vars[0], arith_vars[1], arith_vars[3])
                s2explist.append(s2exp)
                constr_all.append(And([state_1_is_main == states_1_is_main[(dst_state, o)] for o in tuple_options]))
            else:
                s1exp = If(logic_vars[0], arith_vars[0], arith_vars[1])
            s1explist.append(s1exp)

        constr_all.append(Or([states_1[(dst_state, o)] == regact_id[symbol].gen_val(s1explist) for o in tuple_options]))
        if two_slot:
            constr_all.append(Or([states_1[(dst_state, o)] == regact_id[symbol].gen_val(s1explist) for o in tuple_options]))

        s.add(constr_all)                  
        if probe: 
            constraints.extend(constr_all)

        # if (s.check() == sat):
        #     sys.stderr.write("Sat at the %d th symbol.\n" % (num_lists_solved))
        #     num_lists_solved += 1
        # else:
        #     sys.stderr.write("Unsat at the %d th symbol.\n" % (num_lists_solved))
        #     print("-1")
        #     sys.exit()

    if s.check() == sat:
        #print(s.assertions())
        t1 = time.time()
        if probe: 
            for opt, p in ps.items():
                print("%s: %s\n" % (opt, p(And(constraints))))
        sys.stderr.write("Sat with %d regacts.\n" % num_regact)
        model = s.model()
        safety_check = s.model().eval(And(s.assertions()))
        config = toJSON(model, symbols_1, symbols_2, regact_id, states_1, states_2,
                        states_1_is_main, regacts, two_slot, bitvecsize)
        print(True)
        print(safety_check)
        print(t1 - t0)

        if jsonpath == None:
            print(config)
        else:
            with open(jsonpath, "w") as f:
                json.dump(config, f)
        return True, safety_check, (t1 - t0), config
    else:
        t1 = time.time()
        sys.stderr.write("Unsat with %d regacts.\n" % num_regact)

        print(False)
        print(None)
        print(t1 - t0)
        print(None)

        return False, None, (t1 - t0), None

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
    parser.add_argument('--num_split_nodes', type=int, default = 1)
    parser.add_argument('--jsonpath', type=str, default=None)
    args=parser.parse_args()

    # assertion when four_branch == True: two_slot == True, two_cond == True
    assert((args.two_slot and args.two_cond) if args.four_branch else True)

    input_json=json.load(open(args.input))
    createDFA(input_json, args.arith_bin, args.num_arith, args.two_cond, args.two_slot, args.four_branch, 
              args.num_regact, args.bitvecsize, args.timeout, args.probe, args.num_split_nodes, args.jsonpath)

# Classic cases:
# TwoTernary: {arith_bin = True, two_cond = True, two_slot = True, four_branch = True}
# TwoSlot: {arith_bin = True, two_cond = True, two_slot = True, four_branch = False}
# TwoCond: {arith_bin = True, two_cond = True, two_slot = False, four_branch = False}
# Arith: {arith_bin = True, two_cond = False, two_slot = False, four_branch = False}
# Simple: {arith_bin = False, two_cond = False, two_slot = False, four_branch = False}
