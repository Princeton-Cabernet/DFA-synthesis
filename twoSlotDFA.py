from sre_parse import State
from z3 import *
import json
import itertools

ArithOp, (plus, bitxor, bitand) = EnumSort('ArithOp', ('plus', 'bitxor', 'bitand'))
PredOp , (eq, ge, le, neq) = EnumSort('PredOp', ('eq', 'ge', 'le', 'neq'))
LogicOp, (left, booland, boolor) = EnumSort('LogicOp', ('left', 'booland', 'boolor'))
StateOpt, (state_1, state_2, stateconstant) = EnumSort('StateOpt', ('state_1', 'state_2', 'constant')) 
SymbolOpt, (sym_1, sym_2, symconstant) = EnumSort('SymbolOpt', ('sym_1', 'sym_2', 'constant'))

num_regact = 4

RegActChoice, choices = EnumSort('RegActChoice', ['choose_%d' %i for i in range(num_regact)])


num_pred = 2
num_arith = 4
bitvecsize = 4
zero = BitVecVal(0, bitvecsize)
class Pred:
    def __init__(self, reg_act_id, pred_id):
        self.reg_act_id = reg_act_id
        self.pred_id = pred_id
        self.op = Const('pred_op_%d_%d'%(reg_act_id,pred_id), PredOp)
        self.const = BitVec('pred_const_%d_%d'%(reg_act_id,pred_id), bitvecsize)
        self.sym_opt = Const('pred_sym_opt_%d_%d'%(reg_act_id,pred_id), SymbolOpt)
        self.state_opt = Const('pred_state_opt_%d_%d'%(reg_act_id,pred_id), StateOpt)

    def makePredCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        pred_sym = If(self.sym_opt == symconstant, zero, If(self.sym_opt == sym_1, symbol_1, symbol_2))
        pred_state = If(self.state_opt == stateconstant, zero, If(self.state_opt == state_1, pre_state_1, pre_state_2))
        pred_arg = pred_state + pred_sym + self.const
        predicate_eq = If(self.op == eq, pred_arg == zero, False)
        predicate_ge = If(self.op == ge, pred_arg >= zero, False)
        predicate_le = If(self.op == le, pred_arg <= zero, False)
        predicate_neq = If(self.op == neq, pred_arg != zero, False)
        return And(predicate_eq, predicate_ge, predicate_le, predicate_neq)

class Arith:
    def __init__(self, reg_act_id, arith_id):
        self.reg_act_id = reg_act_id
        self.arith_id = arith_id
        self.op = Const('arith_op_%d_%d'%(reg_act_id,arith_id), ArithOp)
        self.sym_opt = Const('arith_sym_opt_%d_%d'%(reg_act_id,arith_id), SymbolOpt)
        self.sym_const = BitVec('arith_sym_const_%d_%d'%(reg_act_id,arith_id), bitvecsize)
        self.state_opt = Const('arith_state_opt_%d_%d'%(reg_act_id,arith_id), StateOpt)
        self.state_const = BitVec('arith_state_const_%d_%d'%(reg_act_id,arith_id), bitvecsize)
    
    def makeArithCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        arith_sym = If(self.sym_opt == symconstant, self.sym_const, If(self.sym_opt == sym_1, symbol_1, symbol_2))
        arith_state = If(self.state_opt == stateconstant, self.state_const, If(self.state_opt == state_1, pre_state_1, pre_state_2))
        arithres = If(self.op == plus, arith_state + arith_sym, If(self.op == bitxor, arith_state ^ arith_sym, arith_state & arith_sym))
        return arithres

class RegAct:
    def __init__(self, reg_act_id):
        self.reg_act_id = reg_act_id
        self.logicop = Const("logicop_%d" % reg_act_id, LogicOp)
        self.preds = [Pred(reg_act_id, i) for i in range(num_pred)]
        self.ariths = [Arith(reg_act_id, i) for i in range(num_arith)]
    
    def makeTransitionCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2, post_state_1, post_state_2):
        leftCond = self.preds[0].makePredCond(pre_state_1, pre_state_2, symbol_1, symbol_2)
        rightCond = self.preds[0].makePredCond(pre_state_1, pre_state_2, symbol_1, symbol_2)
        predCond = If(self.logicop == left, leftCond, If(self.logicop == booland, And(leftCond, rightCond), Or(leftCond, rightCond)))
        arithConds = [ar.makeArithCond(pre_state_1, pre_state_2, symbol_1, symbol_2) for ar in self.ariths]
        branchTrue = And(post_state_1 == arithConds[0], post_state_2 == arithConds[1])
        branchFalse = And(post_state_1 == arithConds[2], post_state_2 == arithConds[3])
        return If(predCond, branchTrue, branchFalse)
        

def createDFA(input):
    constraints = []


    # per RegAct
    reg_acts = [RegAct(0)]

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
    constraints.append(main_state_init == zero)
    for s1, s2 in itertools.product(states_1.keys(), states_1.keys()):
        if s1 != s2: 
            main_state_1 = If(states_1_is_main[s1], states_1[s1], states_2[s1])
            main_state_2 = If(states_1_is_main[s2], states_1[s2], states_2[s2])
            constraints.append(main_state_1 != main_state_2)

    s = Solver()
    s.add(And(constraints))
    reg_adding = 0
    while True:
        #per transition
        for transition in input["transitions"]:
            pre_state_1 = states_1[transition[0]]
            pre_state_2 = states_2[transition[0]]
            symbol_1 = symbols_1[transition[1]]
            symbol_2 = symbols_2[transition[1]]
            post_state_1 = states_1[transition[2]]
            post_state_2 = states_2[transition[2]]
            s.add(If(regact_id[transition[1]] == choices[reg_adding], reg_acts[reg_adding].makeTransitionCond(pre_state_1, pre_state_2, symbol_1, symbol_2, post_state_1, post_state_2), True))
        if s.check() == sat:
            print("sat with %d regacts, check output.txt"%reg_adding)
            m = s.model()
            print(m)
            break
        elif reg_adding < num_regact-1:
            print("Unsat")
            break
        else:
            reg_adding += 1


def main():
    if (len(sys.argv) < 3):
        print ("please give input file and number of bits")
        quit()
    with open(sys.argv[1]) as file:
        input = json.load(file)
    bitvecsize = int(sys.argv[2])
    createDFA(input)

if __name__ == '__main__':
    main()