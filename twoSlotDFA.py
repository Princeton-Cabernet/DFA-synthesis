from sre_parse import State
from z3 import *
import json
import itertools

ArithOp, (plus, bitxor, bitand) = EnumSort('ArithOp', ('plus', 'bitxor', 'bitand'))
PredOp , (eq, ge, le, neq) = EnumSort('PredOp', ('eq', 'ge', 'le', 'neq'))
LogicOp, (left, _, booland, boolor) = EnumSort('LogicOp', ('left', 'right', 'booland', 'boolor'))
StateOpt, (state_1, state_2, stateconstant) = EnumSort('StateOpt', ('state_1', 'state_2', 'stateconstant')) 
SymbolOpt, (sym_1, sym_2, symconstant) = EnumSort('SymbolOpt', ('sym_1', 'sym_2', 'symconstant'))

num_regact = 4
num_pred = 2
num_arith = 4
bitvecsize = 4

RegActChoice, choices = EnumSort('RegActChoice', ['choose_%d' %i for i in range(num_regact)])
zero = BitVecVal(0, bitvecsize)

class Pred:
    def __init__(self, reg_act_id, pred_id):
        self.reg_act_id = reg_act_id
        self.pred_id = pred_id
        self.op = Const('pred_op_%d_%d' % (reg_act_id, pred_id), PredOp)
        self.const = BitVec('pred_const_%d_%d' % (reg_act_id, pred_id), bitvecsize)
        self.sym_opt = Const('pred_sym_opt_%d_%d' % (reg_act_id, pred_id), SymbolOpt)
        self.state_opt = Const('pred_state_opt_%d_%d' % (reg_act_id, pred_id), StateOpt)

    def makePredCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        pred_sym = If(self.sym_opt == symconstant, zero, If(self.sym_opt == sym_1, symbol_1, symbol_2))
        pred_state = If(self.state_opt == stateconstant, zero, If(self.state_opt == state_1, pre_state_1, pre_state_2))
        pred_arg = pred_state + pred_sym + self.const
        predicate_eq = If(self.op == eq, pred_arg == zero, True)
        predicate_ge = If(self.op == ge, pred_arg >= zero, True)
        predicate_le = If(self.op == le, pred_arg <= zero, True)
        predicate_neq = If(self.op == neq, pred_arg != zero, True)
        return And(predicate_eq, predicate_ge, predicate_le, predicate_neq)

    def toJSON(self, model):
        config = { "op": str(model[self.op]),
                   "const": model[self.const].as_long(),
                   "sym_opt": model[self.sym_opt].as_long(),
                   "state_opt": model[self.state_opt].as_long() }
        return config

class Arith:
    def __init__(self, reg_act_id, arith_id):
        self.reg_act_id = reg_act_id
        self.arith_id = arith_id
        self.op = Const('arith_op_%d_%d'% (reg_act_id, arith_id), ArithOp)
        self.sym_opt = Const('arith_sym_opt_%d_%d'% (reg_act_id, arith_id), SymbolOpt)
        self.sym_const = BitVec('arith_sym_const_%d_%d'% (reg_act_id, arith_id), bitvecsize)
        self.state_opt = Const('arith_state_opt_%d_%d'% (reg_act_id, arith_id), StateOpt)
        self.state_const = BitVec('arith_state_const_%d_%d'% (reg_act_id, arith_id), bitvecsize)
    
    def makeArithCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        arith_sym = If(self.sym_opt == symconstant, self.sym_const, If(self.sym_opt == sym_1, symbol_1, symbol_2))
        arith_state = If(self.state_opt == stateconstant, self.state_const, If(self.state_opt == state_1, pre_state_1, pre_state_2))
        arithres = If(self.op == plus, arith_state + arith_sym, 
                   If(self.op == bitxor, arith_state ^ arith_sym, 
                   arith_state & arith_sym))
        return arithres

    def toJSON(self, model):
        config = { "op": str(model[self.op]),
                   "sym_opt": str(model[self.sym_opt]),
                   "sym_const": model[self.sym_const].as_long(),
                   "state_opt": str(model[self.state_opt]),
                   "state_const": model[self.state_const].as_long() }
        return config

class RegAct:
    def __init__(self, reg_act_id):
        self.reg_act_id = reg_act_id
        self.state_1_is_main = Bool("state_1_is_main_%d" % reg_act_id)
        self.logic_op = Const("logic_op_%d" % reg_act_id, LogicOp)
        self.preds = [Pred(reg_act_id, i) for i in range(num_pred)]
        self.ariths = [Arith(reg_act_id, i) for i in range(num_arith)]
    
    def makeTransitionCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2, post_state_1, post_state_2, post_state_1_is_main):
        leftCond = self.preds[0].makePredCond(pre_state_1, pre_state_2, symbol_1, symbol_2)
        rightCond = self.preds[0].makePredCond(pre_state_1, pre_state_2, symbol_1, symbol_2)
        predCond = If(self.logic_op == left, leftCond, If(self.logic_op == booland, And(leftCond, rightCond), Or(leftCond, rightCond)))
        arithConds = [a.makeArithCond(pre_state_1, pre_state_2, symbol_1, symbol_2) for a in self.ariths]
        branchTrue = And(post_state_1 == arithConds[0], post_state_2 == arithConds[1])
        branchFalse = And(post_state_1 == arithConds[2], post_state_2 == arithConds[3])

        return And(If(predCond, branchTrue, branchFalse), self.state_1_is_main == post_state_1_is_main)

    def toJSON(self, model):
        config = { "logic_op" : str(model[self.logic_op]), 
                   "preds" : [p.toJSON() for p in self.preds], 
                   "ariths" : [a.toJSON() for a in self.ariths] }
        return config

def toJSON(symbols_1, symbols_2, regact_id, states_1, states_2, states_1_is_main, reg_acts):
    config = {}
    config["symbols_1"] = { sym : val.as_long() for sym, val in symbols_1 }
    config["symbols_2"] = { sym : val.as_long() for sym, val in symbols_2 }
    config["regact_id"] = { sym : val.as_long() for sym, val in regact_id }
    config["states_1"] = { state : val.as_long() for state, val in states_1 }
    if not states_2.empty():
        config["states_2"] = { state : val.as_long() for state, val in states_2 }
        config["states_1_is_main"] = { state : val.is_true() for state, val in states_1_is_main }
    config["reg_acts"] = [r.toJSON() for r in reg_acts]
    return config


def createDFA(input):
    constraints = []

    # per RegAct
    reg_acts = [RegAct(i) for i in range(num_regact)]

    # per symbol
    symbols_1 = {}
    symbols_2 = {}
    regact_id = {}

    for symbol in input["sigma"]:
        symbols_1[symbol] = BitVec("sym_1_%s" % symbol, bitvecsize)
        symbols_2[symbol] = BitVec("sym_2_%s" % symbol, bitvecsize)
        regact_id[symbol] = Const("regact_%s" % symbol, RegActChoice)

    # per state
    states_1 = {}
    states_2 = {}
    states_1_is_main = {}

    for state in input["states"]:
        states_1[state] = BitVec("state_1_%s" % state, bitvecsize)
        states_2[state] = BitVec("state_2_%s" % state, bitvecsize)
        states_1_is_main[state] = Bool('state_1_is_main_%s' % state)

    state_init_symbol = input["initial"]
    main_state_init = If(states_1_is_main[state_init_symbol], states_1[state_init_symbol], states_2[state_init_symbol])
    constraints.append(main_state_init == BitVecVal(0, bitvecsize))
    for s1, s2 in itertools.product(states_1.keys(), states_1.keys()):
        if s1 != s2: 
            main_state_1 = If(states_1_is_main[s1], states_1[s1], states_2[s1])
            main_state_2 = If(states_1_is_main[s2], states_1[s2], states_2[s2])
            constraints.append(main_state_1 != main_state_2)

    #per transition
    for transition in input["transitions"]:
        pre_state_1 = states_1[transition[0]]
        pre_state_2 = states_2[transition[0]]
        symbol_1 = symbols_1[transition[1]]
        symbol_2 = symbols_2[transition[1]]
        post_state_1 = states_1[transition[2]]
        post_state_2 = states_2[transition[2]]
        post_state_1_is_main = states_1_is_main[transition[2]]

        for i in range(num_regact):
            constraints.append(If(regact_id[transition[1]] == choices[i], 
                                  reg_acts[i].makeTransitionCond(pre_state_1, pre_state_2, symbol_1, symbol_2, 
                                                                 post_state_1, post_state_2, post_state_1_is_main), 
                                  True))
    s = Solver()
    s.add(And(constraints))

    if (s.check() == unsat):
        print("unsat")
    else:
        print("sat")
        m = s.model()
        # print(m)
        config = toJSON(symbols_1, symbols_2, regact_id, states_1, states_2, states_1_is_main, reg_acts)
        print(json.dumps(config))

def main():
    if (len(sys.argv) < 2):
        print ("please give input file")
        quit()
    with open(sys.argv[1]) as file:
        input = json.load(file)
    createDFA(input)

if __name__ == '__main__':
    main()