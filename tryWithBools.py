from z3 import *
import json
import itertools
import argparse

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

class Pred:
    def __init__(self, regact_id, pred_id, arith_bin, two_slot, bitvecsize, doncare_fun = zero):
        self.regact_id = regact_id
        self.pred_id = pred_id
        self.arith_bin = arith_bin
        self.two_slot = two_slot
        self.bitvecsize = bitvecsize
        self.dontcare_val = doncare_fun(bitvecsize)
        self.op_eq = Bool('pred_op_eq_%d_%d' % (regact_id, pred_id))
        self.op_ge = Bool('pred_op_ge_%d_%d' % (regact_id, pred_id))
        self.op_le = Bool('pred_op_le_%d_%d' % (regact_id, pred_id))
        self.op_neq = Bool('pred_op_neq_%d_%d' % (regact_id, pred_id))
        self.const = BitVec('pred_const_%d_%d' % (regact_id, pred_id), bitvecsize)
        self.sym_opt_s1 = Bool('pred_sym_opt_s1_%d_%d' % (regact_id, pred_id))
        self.sym_opt_s2 = Bool('pred_sym_opt_s2_%d_%d' % (regact_id, pred_id))
        self.sym_opt_const = Bool('pred_sym_opt_const_%d_%d' % (regact_id, pred_id))
        self.state_opt_s1 = Bool('pred_state_opt_s1_%d_%d' % (regact_id, pred_id))
        self.state_opt_s2 = Bool('pred_state_opt_s2_%d_%d' % (regact_id, pred_id))
        self.state_opt_const = Bool('pred_state_opt_const_%d_%d' % (regact_id, pred_id))

    #returns list of top level constraints
    def makeDFACond(self):
        constraints = []
        constraints.append(one_is_true_constraints([self.op_eq, self.op_ge, self.op_le, self.op_neq]))
        constraints.append(one_is_true_constraints([self.sym_opt_s1, self.sym_opt_s2, self.sym_opt_const]))
        constraints.append(one_is_true_constraints([self.state_opt_s1, self.state_opt_s2, self.state_opt_const]))
        #if not self.arith_bin:
        #    constraints.append(Or(self.sym_opt == symconstant, self.state_opt == stateconstant))
        #if not self.two_slot:
        #    constraints.append(self.state_opt != state_2)
        return constraints

    def makePredCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2, names):
        constraints = []
        sym_val = BitVec('pred_sym_val_{0}{1}{2}{3}{4}'.format(self.regact_id, self.pred_id, names[0], names[1], names[2]), self.bitvecsize)
        state_val = BitVec('pred_state_val_{0}{1}{2}{3}{4}'.format(self.regact_id, self.pred_id, names[0], names[1], names[2]), self.bitvecsize)
        constraints.append(Implies(self.sym_opt_s1, sym_val == symbol_1))
        constraints.append(Implies(self.sym_opt_s2, sym_val == symbol_2))
        constraints.append(Implies(self.sym_opt_const, sym_val == zero(self.bitvecsize)))
        constraints.append(Implies(self.state_opt_s1, state_val == pre_state_1))
        constraints.append(Implies(self.state_opt_s2, state_val == pre_state_2))
        constraints.append(Implies(self.state_opt_const, state_val == zero(self.bitvecsize)))
        constraints.append(Implies(self.op_eq, (state_val + sym_val + self.const) == zero(self.bitvecsize)))
        constraints.append(Implies(self.op_ge, (state_val + sym_val + self.const) >= zero(self.bitvecsize)))
        constraints.append(Implies(self.op_le, (state_val + sym_val + self.const) <= zero(self.bitvecsize)))
        constraints.append(Implies(self.op_neq, (state_val + sym_val + self.const) != zero(self.bitvecsize)))
        return constraints

    def toJSON(self, model):
        config = { "op": make_string_name_for_enum_bools(model, [(self.op_eq, "=="), (self.op_ge, ">="), (self.op_le, "<="), (self.op_neq, "!=")]),
                   "const": access(model, self.const),
                   "sym_opt": make_string_name_for_enum_bools(model, [(self.sym_opt_s1, "s1"), (self.sym_opt_s2, "s2"), (self.sym_opt_const, "const")]),
                   "state_opt":  make_string_name_for_enum_bools(model, [(self.state_opt_s1, "s1"), (self.state_opt_s2, "s2"), (self.state_opt_const, "const")]) }
        return config

class Arith:
    def __init__(self, regact_id, arith_id, arith_bin, two_slot, bitvecsize, doncare_fun = zero):
        self.regact_id = regact_id
        self.arith_id = arith_id
        self.arith_bin = arith_bin
        self.two_slot = two_slot
        self.bitvecsize = bitvecsize
        self.dontcare_val = doncare_fun(bitvecsize)
        self.op_plus = Bool('arith_op_plus_%d_%d'% (regact_id, arith_id))
        self.op_and = Bool('arith_op_and_%d_%d'% (regact_id, arith_id))
        self.op_xor = Bool('arith_op_xor_%d_%d'% (regact_id, arith_id))
        self.sym_const = BitVec('arith_sym_const_%d_%d'% (regact_id, arith_id), bitvecsize)
        self.state_const = BitVec('arith_state_const_%d_%d'% (regact_id, arith_id), bitvecsize)
        self.sym_opt_s1 = Bool('arith_sym_opt_s1_%d_%d' % (regact_id, arith_id))
        self.sym_opt_s2 = Bool('arith_sym_opt_s2_%d_%d' % (regact_id, arith_id))
        self.sym_opt_const = Bool('arith_sym_opt_const_%d_%d' % (regact_id, arith_id))
        self.state_opt_s1 = Bool('arith_state_opt_s1_%d_%d' % (regact_id, arith_id))
        self.state_opt_s2 = Bool('arith_state_opt_s2_%d_%d' % (regact_id, arith_id))
        self.state_opt_const = Bool('arith_state_opt_const_%d_%d' % (regact_id, arith_id))
    
    #returns list of top level constraints
    def makeDFACond(self):
        constraints = []
        constraints.append(one_is_true_constraints([self.op_plus, self.op_and, self.op_xor]))
        constraints.append(one_is_true_constraints([self.sym_opt_s1, self.sym_opt_s2, self.sym_opt_const]))
        constraints.append(one_is_true_constraints([self.state_opt_s1, self.state_opt_s2, self.state_opt_const]))
        #if not self.arith_bin:
        #    constraints.append(And(Or(And(self.sym_opt == symconstant, self.sym_const == zero(self.bitvecsize)), 
        #                       And(self.state_opt == stateconstant, self.state_const == zero(self.bitvecsize))),
        #                self.op == bitxor))
        #if not self.two_slot:
        #    constraints.append(self.state_opt != state_2)
        return constraints

    def makeArithCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2, names):

        sym_val = BitVec('arith_sym_val_{0}{1}{2}{3}{4}'.format(self.regact_id, self.arith_id, names[0], names[1], names[2]), self.bitvecsize)
        state_val = BitVec('arith_state_val_{0}{1}{2}{3}{4}'.format(self.regact_id, self.arith_id, names[0], names[1], names[2]), self.bitvecsize)
        arith_res = BitVec('arith_res_{0}{1}{2}{3}{4}'.format(self.regact_id, self.arith_id, names[0], names[1], names[2]), self.bitvecsize)
        constraints = []
        constraints.append(Implies(self.sym_opt_s1, sym_val == symbol_1))
        constraints.append(Implies(self.sym_opt_s2, sym_val == symbol_2))
        constraints.append(Implies(self.sym_opt_const, sym_val == zero(self.bitvecsize)))
        constraints.append(Implies(self.state_opt_s1, state_val == pre_state_1))
        constraints.append(Implies(self.state_opt_s2, state_val == pre_state_2))
        constraints.append(Implies(self.state_opt_const, state_val == zero(self.bitvecsize)))
        constraints.append(Implies(self.op_plus, arith_res == sym_val + state_val))
        constraints.append(Implies(self.op_and, arith_res == sym_val & state_val))
        constraints.append(Implies(self.op_xor, arith_res == sym_val ^ state_val))
        return (constraints, arith_res)

    def toJSON(self, model):
        config = { "op": make_string_name_for_enum_bools(model, [(self.op_plus, "+"), (self.op_and, "&"), (self.op_xor, "^")]),
                   "sym_opt": make_string_name_for_enum_bools(model, [(self.sym_opt_s1, "s1"), (self.sym_opt_s2, "s2"), (self.sym_opt_const, "const")]),
                   "sym_const": access(model, self.sym_const),
                   "state_opt":  make_string_name_for_enum_bools(model, [(self.state_opt_s1, "s1"), (self.state_opt_s2, "s2"), (self.state_opt_const, "const")]),
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
        #self.num_logical_op = 2 if four_branch else 1
        self.preds = [Pred(regact_id, i, arith_bin, two_slot, bitvecsize) for i in range(self.num_pred)]
        self.ariths = [Arith(regact_id, i, arith_bin, two_slot, bitvecsize) for i in range(self.num_arith)]
        #self.logic_ops = [Const("logic_op_%d_%d" % (regact_id, i), LogicOp) for i in range(self.num_logical_op)]
        self.logic_op_left = Bool("logic_op_left_%d" % regact_id)
        self.logic_op_and = Bool("logic_op_and_%d" % regact_id)
        self.logic_op_or = Bool("logic_op_or_%d" % regact_id)
        self.state_1_is_main = Bool("state_1_is_main_%d" % regact_id)
    
    def makeDFACond(self):
        constraints = []
        for p in self.preds:
            constraints.extend(p.makeDFACond())
        for a in self.ariths:
            constraints.extend(a.makeDFACond())
        constraints.append(one_is_true_constraints([self.logic_op_and, self.logic_op_left, self.logic_op_or]))
        #if not self.two_cond:
        #    constraints.append(self.logic_ops[0] == left)
        #if not self.two_slot:
        #    constraints.append(self.state_1_is_main)
        return constraints

    def makeTransitionCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2, post_state_1, post_state_2, post_state_1_is_main, names):
        pred_conds= [p.makePredCond(pre_state_1, pre_state_2, symbol_1, symbol_2, names) for p in self.preds]
        arith_exprs= [a.makeArithCond(pre_state_1, pre_state_2, symbol_1, symbol_2, names) for a in self.ariths]
        pred_val = Bool('top_pred_val_{0}{1}{2}{3}'.format(self.regact_id, names[0], names[1], names[2]))
        constraints= []
        for conds in arith_exprs:
            constraints.extend(conds[0])
        if self.two_cond:
            constraints.append(Implies(self.logic_op_left, pred_val == And(pred_conds[0])))
            constraints.append(Implies(self.logic_op_and, pred_val == And(And(pred_conds[0]), And(pred_conds[1]))))
            constraints.append(Implies(self.logic_op_or, pred_val == Or(And(pred_conds[0]), And(pred_conds[1]))))
        else:
            constraints.append(pred_val == And(pred_conds[0]))
        
        if self.two_slot:
            #if self.four_branch:
            #    constraints.append(If(pred_combos[0], post_state_1 == arith_exprs[0], post_state_1 == arith_exprs[2]))
            #    constraints.append(If(pred_combos[1], post_state_2 == arith_exprs[1], post_state_2 == arith_exprs[3]))
            #else:
            branch_true = And(post_state_1 == arith_exprs[0][1], post_state_2 == arith_exprs[1][1])
            branch_false = And(post_state_1 == arith_exprs[2][1], post_state_2 == arith_exprs[3][1])
            constraints.append(If(pred_val, branch_true, branch_false))
        else:
            branch_true = And(post_state_1 == arith_exprs[0][1])
            branch_false = And(post_state_1 == arith_exprs[1][1])
            constraints.append(If(pred_val, branch_true, branch_false))
        #constraints.append(self.state_1_is_main == post_state_1_is_main)
        return And(constraints)

    def toJSON(self, model):
        logic_op_string = ""
        
        config = { "logic_ops" : make_string_name_for_enum_bools(model, [(self.logic_op_left, "left"), (self.logic_op_and, "and"), (self.logic_op_or, "or")]), 
                   "preds" : [p.toJSON(model) for p in self.preds], 
                   "ariths" : [a.toJSON(model) for a in self.ariths],
                   "state_1_is_main" : bool(model[self.state_1_is_main]) }
        return config

def toJSON(model, symbols_1, symbols_2, regact_id, states_1, states_2, states_1_is_main, regacts, two_slot, bitvecsize):
    config = {}
    config["bitvecsize"] = bitvecsize
    config["symbols_1"] = { sym : access(model, val) for sym, val in symbols_1.items() }
    config["symbols_2"] = { sym : access(model, val) for sym, val in symbols_2.items() }
    regdict = {}
    for keytuple, val in regact_id.items():
        if access(model, val) == True:
            regdict[keytuple[0]] = keytuple[1]
    config["regact_id"] = regdict
    config["states_1"] = { state : access(model, val) for state, val in states_1.items() }
    if two_slot:
        config["states_2"] = { state : access(model, val) for state, val in states_2.items() }
        config["states_1_is_main"] = { state : bool(model[val]) for state, val in states_1_is_main.items() }
    config["regacts"] = [r.toJSON(model) for r in regacts]
    return config

def createDFA(input, arith_bin, two_cond, two_slot, four_branch, num_regact, bitvecsize):
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

    for symbol in input["sigma"]:
        symbols_1[symbol] = BitVec("sym_1_%s" % symbol, bitvecsize)
        symbols_2[symbol] = BitVec("sym_2_%s" % symbol, bitvecsize)
        for j in range(num_regact):
            regact_id[(symbol, j)] = Bool("regact_%s%d" % (symbol, j))
        constraints.append(one_is_true_constraints([regact_id[symbol, i] for i in range(num_regact)]))

    # per state
    states_1 = {}
    states_2 = {}
    states_1_is_main = {}

    for state in input["states"]:
        states_1[state] = BitVec("state_1_%s" % state, bitvecsize)
        states_2[state] = BitVec("state_2_%s" % state, bitvecsize)
        #states_1_is_main[state] = Bool('state_1_is_main_%s' % state)

    for s1, s2 in itertools.product(states_1.keys(), states_1.keys()):
        if (s1 != s2):
            constraints.append(states_1[s1] != states_1[s2])
    #    if s1 != s2: 
    #        main_state_1 = If(states_1_is_main[s1], states_1[s1], states_2[s1])
    #        main_state_2 = If(states_1_is_main[s2], states_1[s2], states_2[s2])
    #        constraints.append(main_state_1 != main_state_2)

    s = Solver()
    s.add(constraints)

    for transition in input["transitions"]:
            pre_state_1 = states_1[transition[0]]
            pre_state_2 = states_2[transition[0]]
            symbol_1 = symbols_1[transition[1]]
            symbol_2 = symbols_2[transition[1]]
            post_state_1 = states_1[transition[2]]
            post_state_2 = states_2[transition[2]]
            #post_state_1_is_main = states_1_is_main[transition[2]]
            for j in range(num_regact):
                s.add(Implies(regact_id[(transition[1], j)], regacts[j].makeTransitionCond(pre_state_1, pre_state_2, symbol_1, symbol_2, post_state_1,\
                     post_state_2, True, (transition[0], transition[1], transition[2]))))
    #print(s)
    if s.check() == sat:
        sys.stderr.write("Sat with %d regacts." % num_regact)
        model = s.model()
        config = toJSON(model, symbols_1, symbols_2, regact_id, states_1, states_2,
                     states_1_is_main, regacts, two_slot, bitvecsize)
        print(json.dumps(config))
        #print(model)
    else:
        sys.stderr.write("unsat")
        print("-1")


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
    args=parser.parse_args()
    # assertion when four_branch == True: two_slot == True, two_cond == True
    assert(args.two_slot and args.two_cond if args.four_branch else True)

    input_json=json.load(open(args.input))
    createDFA(input_json, args.arith_bin, args.two_cond, args.two_slot, args.four_branch, args.num_regact, args.bitvecsize)

# Classic cases:
# TwoTernary: {arith_bin = True, two_cond = True, two_slot = True, four_branch = True}
# TwoSlot: {arith_bin = True, two_cond = True, two_slot = True, four_branch = False}
# TwoCond: {arith_bin = True, two_cond = True, two_slot = False, four_branch = False}
# Arith: {arith_bin = True, two_cond = False, two_slot = False, four_branch = False}
# Simple: {arith_bin = False, two_cond = False, two_slot = False, four_branch = False}