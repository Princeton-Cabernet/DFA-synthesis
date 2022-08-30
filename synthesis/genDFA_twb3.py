from ast import If
import traceback
from z3 import *
import json
import itertools
import argparse
import random
import time

# constant zero
def zero(bitvecsize): return BitVecVal(0, bitvecsize)

def access(model, val):
    return str(model.eval(val))

# For bools a,b,c return ((a & !b & !c) || (!a ^ b ^ !c) || (!a ^ !b ^ c))
def one_is_true_constraints(list_of_bools):
    ans = []
    for b in list_of_bools:
        clause = [b]
        for oth in list_of_bools:
            if (not(b == oth)):
                clause.append(Not(oth))
        ans.append(And(clause))
    return Or(ans)

#Input is a list of pairs (z3Bool, stringIfTrue). Returns the string corresponding to the first true
def make_string_name_for_enum_bools(model, list_of_pairs):
    for pair in list_of_pairs:
        if model.eval(pair[0]):
            return pair[1]

def print_string_name_ordered_from_0(list_of_bool_names, list_of_string_names, model):
    try:
        fst = bool(model[list_of_bool_names[0]])
        num_opts = len(list_of_string_names)
        if num_opts == 6:
            idx = 0
            if bool(model[list_of_bool_names[0]]) and bool(model[list_of_bool_names[1]]): idx = 0
            elif bool(model[list_of_bool_names[0]]) and not bool(model[list_of_bool_names[1]]): idx = 1
            elif not bool(model[list_of_bool_names[0]]) and bool(model[list_of_bool_names[1]]) and bool(model[list_of_bool_names[2]]): idx = 2
            elif not bool(model[list_of_bool_names[0]]) and bool(model[list_of_bool_names[1]]) and not bool(model[list_of_bool_names[2]]): idx = 3
            elif not bool(model[list_of_bool_names[0]]) and not bool(model[list_of_bool_names[1]]) and bool(model[list_of_bool_names[2]]): idx = 4
            elif not bool(model[list_of_bool_names[0]]) and not bool(model[list_of_bool_names[1]]) and not bool(model[list_of_bool_names[2]]): idx = 5
            return list_of_string_names[idx]
        else:
            if num_opts == 3 and fst:
                idx = 2
            elif num_opts > 2:
                snd = bool(model[list_of_bool_names[1]])
                if(fst):
                    idx = 3 if snd else 2
                else:
                    idx = 1 if snd else 0
            else:
                idx = 1 if fst else 0
            return list_of_string_names[min(len(list_of_string_names) - 1, idx)]
    except:
        import traceback
        traceback.print_exc()
        return "unknown"


def sort_by_letter(transitions, symbols_order):
    sorted = []
    for sym in symbols_order:
        for trans in transitions:
            if trans[1] == sym:
                sorted.append(trans)
    return sorted

class Pred:
    def __init__(self, regact_id, pred_id, arith_bin, two_slot, bitvecsize, doncare_fun = zero):
        self.regact_id = regact_id
        self.pred_id = pred_id
        self.arith_bin = arith_bin
        self.two_slot = two_slot
        self.bitvecsize = bitvecsize
        #self.dontcare_val = doncare_fun(bitvecsize)
        #11 -> eq; 10 -> geq; 01 -> leq; 00 -> neq
        self.op_0 = Bool('pred_op_0_%d_%d' % (regact_id, pred_id))
        self.op_1 = Bool('pred_op_1_%d_%d' % (regact_id, pred_id))
        #self.op_le = Bool('pred_op_le_%d_%d' % (regact_id, pred_id))
        #self.op_neq = Bool('pred_op_neq_%d_%d' % (regact_id, pred_id))
        self.const = BitVec('pred_const_%d_%d' % (regact_id, pred_id), bitvecsize)
        self.sym_opt_const = Bool('pred_sym_opt_const_%d_%d' % (regact_id, pred_id))
        self.sym_opt_which_sym = Bool('pred_sym_opt_which_sym_%d_%d' % (regact_id, pred_id)) #f/sym1 is true, g/sym2 is false
        #self.sym_opt_const = Bool('pred_sym_opt_const_%d_%d' % (regact_id, pred_id))    //CONST/LEAVEOFF is both above false
        self.state_opt_const = Bool('pred_state_opt_const_%d_%d' % (regact_id, pred_id))
        if two_slot:
            self.state_opt_which_state = Bool('pred_state_opt_which_state_%d_%d' % (regact_id, pred_id)) # true is lo, false is high
        #self.state_opt_const = Bool('pred_state_opt_const_%d_%d' % (regact_id, pred_id))   //CONST/LEAVEOFF is above false

    #returns list of top level constraints
    def makeDFACond(self):
        constraints = []
        #.append(one_is_true_constraints([self.op_ge, self.op_eq, self.op_neq]))
        #constraints.append(one_is_true_constraints([self.sym_opt_s1, self.sym_opt_s2, self.sym_opt_const]))
        #if self.two_slot:
            #constraints.append(one_is_true_constraints([self.state_opt_s1, self.state_opt_s2, self.state_opt_const]))
        #else:
            #constraints.append(one_is_true_constraints([self.state_opt_s1, self.state_opt_const]))
        #if not self.arith_bin:
        #    constraints.append(Or(self.sym_opt == symconstant, self.state_opt == stateconstant))
        #if not self.two_slot:
        #    constraints.append(self.state_opt != state_2)
        return constraints

    def makePredCond(self, pre_state_tuple, symbol_1, symbol_2):
        if self.two_slot:
            exp_state_choice = If(self.state_opt_which_state, pre_state_tuple[0], pre_state_tuple[1])
        else:
            exp_state_choice = pre_state_tuple[0]
        sym_choice = If(self.sym_opt_which_sym, symbol_1, symbol_2)
        pred_LHS = If(self.state_opt_const, If(self.sym_opt_const, self.const, sym_choice + self.const), exp_state_choice + If(self.sym_opt_const, self.const, sym_choice + self.const))
        pred_val = If(self.op_0,If(self.op_1, pred_LHS ==0, pred_LHS >= 0), If(self.op_1, pred_LHS <= 0, pred_LHS != 0))
        return pred_val

    def toJSON(self, model):
        config = { "op": print_string_name_ordered_from_0([self.op_0, self.op_1], ["neq", "le", "ge", "eq"], model),
                   "const": access_int(model, self.const),
                   "sym_opt": print_string_name_ordered_from_0([self.sym_opt_const, self.sym_opt_which_sym], ["s2", "s1", "const"], model),
                   "state_opt":  print_string_name_ordered_from_0([self.state_opt_const, self.state_opt_which_state] if self.two_slot else [self.state_opt_const], ["s2", "s1", "const"] if self.two_slot else ["s1", "const"], model)}
        return config

class Arith:
    def __init__(self, regact_id, arith_id, arith_bin, two_slot, bitvecsize, doncare_fun = zero):
        self.regact_id = regact_id
        self.arith_id = arith_id
        self.arith_bin = arith_bin
        self.two_slot = two_slot
        self.bitvecsize = bitvecsize
        self.dontcare_val = doncare_fun(bitvecsize)
        self.op_1 = Bool('arith_op_1_%d_%d'% (regact_id, arith_id)) #00 -> IR , 01 -> XOR, 10 -> AND, 11 -> Plus
        self.op_2 = Bool('arith_op_2_%d_%d'% (regact_id, arith_id))
        self.op_3 = Bool('arith_op_3_%d_%d'% (regact_id, arith_id))
        #self.op_xor = Bool('arith_op_xor_%d_%d'% (regact_id, arith_id)) //XOR is else case
        self.sym_const = BitVec('arith_sym_const_%d_%d'% (regact_id, arith_id), bitvecsize)
        self.state_const = BitVec('arith_state_const_%d_%d'% (regact_id, arith_id), bitvecsize)
        self.sym_opt_const = Bool('arith_sym_opt_const_%d_%d' % (regact_id, arith_id))
        self.sym_opt_which_sym = Bool('arith_sym_opt_which_sym_%d_%d' % (regact_id, arith_id))
        #self.sym_opt_const = Bool('arith_sym_opt_const_%d_%d' % (regact_id, arith_id)) //CONST is else case
        self.state_opt_const = Bool('arith_state_opt_const_%d_%d' % (regact_id, arith_id))
        if two_slot:
            self.state_opt_which_state = Bool('arith_state_opt_which_state_%d_%d' % (regact_id, arith_id))
        #self.state_opt_const = Bool('arith_state_opt_const_%d_%d' % (regact_id, arith_id)) //CONST is else case
    
    #returns list of top level constraints
    def makeDFACond(self):
        constraints = []
        return constraints

    def makeArithCond(self, pre_state_tuple, symbol_1, symbol_2):
        if self.two_slot:
            exp_state_choice = If(self.state_opt_which_state, pre_state_tuple[0], pre_state_tuple[1])
        else:
            exp_state_choice = pre_state_tuple[0]
        sym_choice = If(self.sym_opt_const,self.sym_const, If(self.sym_opt_which_sym, symbol_1, symbol_2))
        state_choice = If(self.state_opt_const, self.state_const, exp_state_choice)
        arith_val = If(self.op_1, If(self.op_2, state_choice + sym_choice, state_choice & sym_choice), If(self.op_2, If(self.op_3, state_choice ^ sym_choice, state_choice | sym_choice), If(self.op_3, state_choice - sym_choice, sym_choice - state_choice)))
        return arith_val

    def toJSON(self, model):
        config = { "op": print_string_name_ordered_from_0([self.op_1, self.op_2, self.op_3], ["plus", "and", "xor", "or", "subr", "sub"], model),
                   "sym_const": access_int(model, self.sym_const),
                   "sym_opt": print_string_name_ordered_from_0([self.sym_opt_const, self.sym_opt_which_sym], ["s2", "s1", "const"], model),
                   "state_opt":  print_string_name_ordered_from_0([self.state_opt_const, self.state_opt_which_state] if self.two_slot else [self.state_opt_const], ["s2", "s1", "const"] if self.two_slot else ["s1", "const"], model), 
                   "state_const": access_int(model, self.state_const) }
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
        #self.num_logical_op = 2 if four_branch else 1
        self.preds = [Pred(regact_id, i, arith_bin, two_slot, bitvecsize) for i in range(self.num_pred)]
        self.ariths = [Arith(regact_id, i, arith_bin, two_slot, bitvecsize) for i in range(self.num_arith)]
        #self.logic_ops = [Const("logic_op_%d_%d" % (regact_id, i), LogicOp) for i in range(self.num_logical_op)]
        if(two_cond):
            self.logic_op_left = Bool("logic_op_left_%d" % regact_id)
            self.logic_op_and = Bool("logic_op_and_%d" % regact_id)
        #self.logic_op_or = Bool("logic_op_or_%d" % regact_id)           //OR is both above false
        #self.state_1_is_main = Bool("state_1_is_main_%d" % regact_id)
    
    def makeDFACond(self):
        constraints = []
        for p in self.preds:
            constraints.extend(p.makeDFACond())
        for a in self.ariths:
            constraints.extend(a.makeDFACond())
        return constraints

    def makeTransitionCond(self, pre_state_tuple, symbol_1, symbol_2, name):
        constraints = []
        pred_conds= [p.makePredCond(pre_state_tuple, symbol_1, symbol_2) for p in self.preds]
        pred1 = Bool("trans_top_pred_val_left_{0}{1}".format(self.regact_id, name))
        constraints.append(pred1 == pred_conds[0])
        if self.two_cond:
            pred2 = Bool("trans_top_pred_val_right_{0}{1}".format(self.regact_id, name))
            constraints.append(pred2 == pred_conds[1])
            pred_val = If(self.logic_op_left, pred1, If(self.logic_op_and, And(pred1, pred2), Or(pred1, pred2)))
        else:
            pred_val = pred1
        avals = [] 
        for arith in self.ariths:
            aval = BitVec("val_arith_{0}{1}{2}".format(self.regact_id, arith.arith_id, name), self.bitvecsize)
            avals.append(aval)
            constraints.append(aval == arith.makeArithCond(pre_state_tuple, symbol_1, symbol_2))
        if (self.two_slot):
            return [constraints, If(pred_val, avals[0], avals[2]), If(pred_val, avals[1], avals[3])]
        else:
            return [constraints, If(pred_val, avals[0], avals[1])]

    def toJSON(self, model):
        logic_op_string = ""
        
        config = { "logic_ops" : [print_string_name_ordered_from_0([self.logic_op_left, self.logic_op_and], ["or", "and", "left"], model) if self.two_cond else "left"], 
                   "preds" : [p.toJSON(model) for p in self.preds], 
                   "ariths" : [a.toJSON(model) for a in self.ariths]}
        return config

def access_int(model, val):
    return model[val].as_long() if (model[val] != None) else None

def toJSON(model, symbols_1, symbols_2, regact_id, states_1, states_2, regacts, two_slot, bitvecsize, num_regacts):
    config = {}
    config["bitvecsize"] = bitvecsize
    config["symbols_1"] = { sym : access_int(model, val) for sym, val in symbols_1.items() }
    config["symbols_2"] = { sym : access_int(model, val) for sym, val in symbols_2.items() }
    numregbool = 2 if num_regacts > 2 else 1
    if(num_regacts > 1):
        regdict = {sym : int(print_string_name_ordered_from_0([regact_id[(sym, reg)] for reg in range(numregbool)], [i for i in range(num_regacts)], model)) for sym in symbols_1.keys()}
    else:
        regdict = {sym : 0 for sym in symbols_1.keys()}
    config["regact_id"] = regdict
    config["states_1"] = { pair_to_string(state, has_suffix_for_0=True) : access_int(model, val) for state, val in states_1.items() }
    if two_slot:
       config["states_2"] = { pair_to_string(state, has_suffix_for_0=True) : access_int(model, val) for state, val in states_2.items() }
    #   config["states_1_is_main"] = { state : bool(model[val]) for state, val in states_1_is_main.items() }
    config["regacts"] = [r.toJSON(model) for r in regacts]
    return config

def pair_to_string(state_pair, has_suffix_for_0=False):
    if state_pair[1]==0 and has_suffix_for_0==False: return state_pair[0]
    return "%s_%d" % state_pair

import collections

def createDFA(input, arith_bin, two_cond, two_slot, four_branch, num_regact, bitvecsize, num_split_nodes,  jsonpath=None):
    t0 = time.time()
    states, symbols, transitions = input["states"], input["sigma"], input["transitions"]

    # graph analysis, in_degree
    in_symbols=collections.defaultdict(set)
    out_edges=collections.defaultdict(set)
    for src,sym,dst in transitions:
        in_symbols[dst].add(sym)
        out_edges[src].add(dst)
    is_split=lambda dst:(len(out_edges[dst])<= 2) and (len(in_symbols[dst])>1)
    # split_to_str=lambda s:(f'spl[{s[0]}(<-{s[1]})]' if s[1]!=None else s[0])
    expanded_states=set()
    split_nodes={}
    for dst in states:
        # print(out_edges[dst], len(in_symbols[dst]))
        if is_split(dst):
            sys.stderr.write(f'notice: state {dst} is split into {num_split_nodes} nodes.\n')
            split_nodes[dst]=[(dst, i) for i in range(num_split_nodes)]
        else:
            split_nodes[dst]=[(dst, 0)]
        expanded_states.update(split_nodes[dst])
    expanded_transitions = []
    for src, sym, dst in transitions:
        if is_split(src):
            expanded_transitions.extend([[(src, i), sym, dst] for i in range(num_split_nodes)])
        else:
            expanded_transitions.append([(src, 0), sym, dst])


    # constraints
    constraints = []

    # per RegAct
    regacts = [RegAct(i, arith_bin, two_cond, two_slot, four_branch, bitvecsize) for i in range(num_regact)]
    for regact in regacts:
        constraints.extend(regact.makeDFACond())

    # Regact choice sort
    #RegActChoice, choices = EnumSort('RegActChoice', ['choose_%d' %i for i in range(num_regact)])

    # per symbol
    symbols_1 = {}
    symbols_2 = {}
    regact_id = {}

    for symbol in symbols:
        symbols_1[symbol] = BitVec("sym_1_%s" % symbol, bitvecsize)
        symbols_2[symbol] = BitVec("sym_2_%s" % symbol, bitvecsize)
        if(num_regact > 2):
            regact_id[(symbol, 1)] = Bool("regact_%s1" % symbol)
        if(num_regact > 1):
            regact_id[(symbol,0)] = Bool("regact_%s0" % symbol)
        # constraints.append(one_is_true_constraints([regact_id[(symbol, i)] for i in range(num_regact)]))

    # per state
    states_1 = {}
    states_2 = {}

    for state in expanded_states:
        states_1[state] = BitVec("state_1_%s" % pair_to_string(state), bitvecsize)
        if state[0] == input["initial"]:
            constraints.append(states_1[state] == BitVecVal(0, bitvecsize))
        if two_slot:
            states_2[state] = BitVec("state_2_%s" % pair_to_string(state), bitvecsize)

    for s1, s2 in itertools.combinations(states_1.keys(), 2):
        if s1 != s2: 
            main_state_1 = states_1[s1]
            main_state_2 = states_1[s2]
            if s1[0] != s2[0]:
                constraints.append(main_state_1 != main_state_2)

    s = Then('simplify', 'solve-eqs', 'bit-blast', 'qffd', 'sat').solver() 
    s.set("timeout", 1800 * 1000)
    s.add(And(constraints))
    for transition in expanded_transitions:
        src_state_split, symbol, dst_state = transition
        sym = symbol # an alias, for later clauses in the loop
        pre_state_1 = states_1[src_state_split]
        if two_slot:
            pre_state_2 = states_2[src_state_split]
            pre_state_tuple = [pre_state_1, pre_state_2]
        else:
            pre_state_tuple = [pre_state_1]
        symbol_1 = symbols_1[symbol]
        symbol_2 = symbols_2[symbol]

        tuple_options = range(num_split_nodes) if is_split(dst_state) else [0]
        reg_cons_this_trans = []
        for reg in range(num_regact):
            name = "%s%s%s" % (pair_to_string(src_state_split), symbol, dst_state)
            reg_cons_this_trans.append(regacts[reg].makeTransitionCond(pre_state_tuple, symbol_1, symbol_2, name))

        def ReduceOr(cons_list_of_and):
            if len(cons_list_of_and)==1:
                only_c=cons_list_of_and[0]
                for c in only_c:
                    s.add(c)
            else:
                or_c=[]
                for tup in cons_list_of_and:
                    if len(tup)==0:
                        or_c.append(tup[0])
                    else:
                        or_c.append(And(tup))
                s.add(Or(or_c))

        if(num_regact == 4):
            if two_slot:
                ReduceOr([[states_1[(dst_state, o)] == If(regact_id[(sym, 0)], 
                    If(regact_id[(sym, 1)], reg_cons_this_trans[3][1], reg_cons_this_trans[2][1]), 
                    If(regact_id[(sym, 1)], reg_cons_this_trans[1][1], reg_cons_this_trans[0][1])),
                        states_2[(dst_state, o)] == If(regact_id[(sym, 0)], 
                    If(regact_id[(sym, 1)], reg_cons_this_trans[3][2], reg_cons_this_trans[2][2]), 
                    If(regact_id[(sym, 1)], reg_cons_this_trans[1][2], reg_cons_this_trans[0][2]))] for o in tuple_options]) 
            else:
                ReduceOr([[states_1[(dst_state, o)] == If(regact_id[(sym, 0)], 
                    If(regact_id[(sym, 1)], reg_cons_this_trans[3][1], reg_cons_this_trans[2][1]), 
                    If(regact_id[(sym, 1)], reg_cons_this_trans[1][1], reg_cons_this_trans[0][1]))] for o in tuple_options]) 
        elif(num_regact == 3):
            if two_slot:
                ReduceOr([[states_1[(dst_state, o)] == If(regact_id[(sym, 0)], reg_cons_this_trans[2][1], 
                    If(regact_id[(sym, 1)], reg_cons_this_trans[1][1], reg_cons_this_trans[0][1])),
                        states_2[(dst_state, o)] == If(regact_id[(sym, 0)], reg_cons_this_trans[2][2],
                    If(regact_id[(sym, 1)], reg_cons_this_trans[1][2], reg_cons_this_trans[0][2]))] for o in tuple_options]) 
            else:
                ReduceOr([[states_1[(dst_state, o)] == If(regact_id[(sym, 0)], reg_cons_this_trans[2][1], 
                       If(regact_id[(sym, 1)], reg_cons_this_trans[1][1], reg_cons_this_trans[0][1]))] for o in tuple_options]) 
        elif(num_regact == 2):
            if two_slot:
                ReduceOr([[states_1[(dst_state, o)] == If(regact_id[(sym, 0)], reg_cons_this_trans[1][1], reg_cons_this_trans[0][1]),
                              states_2[(dst_state, o)] == If(regact_id[(sym, 0)], reg_cons_this_trans[1][2], reg_cons_this_trans[0][2])] for o in tuple_options])
            else:
                ReduceOr([[states_1[(dst_state, o)] == If(regact_id[(sym, 0)], reg_cons_this_trans[1][1], reg_cons_this_trans[0][1])] for o in tuple_options])
        else:
            if two_slot:
                ReduceOr([[states_1[(dst_state, o)] == reg_cons_this_trans[0][1], states_2[(dst_state, o)] == reg_cons_this_trans[0][2]] for o in tuple_options])
            else:
                ReduceOr([[states_1[(dst_state, o)] == reg_cons_this_trans[0][1]] for o in tuple_options])
        for reg_cons in reg_cons_this_trans:
            s.add(reg_cons[0]) 

    print(s.assertions())
    if s.check() == sat:
        t1 = time.time()
        sys.stderr.write("Sat with %d regacts." % num_regact)
        model = s.model()
        config = toJSON(model, symbols_1, symbols_2, regact_id, states_1, states_2, regacts, two_slot, bitvecsize, num_regact)
        safety_check = bool(model.eval(And(s.assertions())))
        print(True)
        print(safety_check)
        print(t1-t0)
        # print(config)

        if jsonpath == None:
            print(json.dumps(config))
        else:
            with open(jsonpath, "w") as f:
                json.dump(config, f)

        return True, safety_check, (t1 - t0), config
        #print(model)
    else:
        t1 = time.time()
        sys.stderr.write("Unsat with %d regacts.\n" % num_regact)
        sys.stderr.write(str(t1 - t0))

        print(False)
        print(None)
        print(t1-t0)
        # print(None)

        return False, None, (t1 - t0), None


    """while True:
        #per transition
        
            s.push()
            for symbol in input["sigma"]:
                choice_constraints = []
                for i in range(reg_adding + 1):
                    choice_constraints.append(regact_id[symbol] == choices[i])
                s.add(Or(choice_constraints))
        if s.check() == sat:
            sys.stderr.write("Sat with %d regacts." % (reg_adding + 1))
            model = s.model()
            config = toJSON(model, symbols_1, symbols_2, regact_id, states_1, states_2,
                            states_1_is_main, regacts[: reg_adding + 1], two_slot, bitvecsize)
            print(json.dumps(config))
            break
        elif reg_adding >= num_regact - 1:
            sys.stderr.write("unsat")
            print("-1")
            break
        else:
            s.pop()
            reg_adding += 1"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create DFA configurations.')
    parser.add_argument('input', type=str)
    parser.add_argument('--arith_bin', action='store_true')
    parser.add_argument('--two_cond', action='store_true')
    parser.add_argument('--two_slot', action='store_true')
    parser.add_argument('--four_branch', action='store_true')
    parser.add_argument('--num_regact', type=int, default=1)
    parser.add_argument('--bitvecsize', type=int, default=8)
    parser.add_argument('--num_split_nodes', type=int, default = 1)
    parser.add_argument('--jsonpath', type=str, default=None)
    
    
    args=parser.parse_args()
    # assertion when four_branch == True: two_slot == True, two_cond == True
    assert(args.two_slot and args.two_cond if args.four_branch else True)

    input_json=json.load(open(args.input))
    createDFA(input_json, args.arith_bin, args.two_cond, args.two_slot, args.four_branch, args.num_regact,
        args.bitvecsize, args.num_split_nodes, args.jsonpath)

# Classic cases:
# TwoTernary: {arith_bin = True, two_cond = True, two_slot = True, four_branch = True}
# TwoSlot: {arith_bin = True, two_cond = True, two_slot = True, four_branch = False}
# TwoCond: {arith_bin = True, two_cond = True, two_slot = False, four_branch = False}
# Arith: {arith_bin = True, two_cond = False, two_slot = False, four_branch = False}
# Simple: {arith_bin = False, two_cond = False, two_slot = False, four_branch = False}
