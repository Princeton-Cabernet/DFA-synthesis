from sre_parse import State
from z3 import *
import json
import itertools

ArithOp, (plus, bitxor, bitand) = EnumSort('ArithOp', ('plus', 'bitxor', 'bitand'))
PredOp , (eq, ge, le, neq) = EnumSort('PredOp', ('eq', 'ge', 'le', 'neq'))
LogicOp, (left, right, booland, boolor) = EnumSort('LogicOp', ('left', 'right', 'booland', 'boolor'))
StateOpt, (state_1, state_2, constant) = EnumSort('StateOpt', ('state_1', 'state_2', 'constant')) 
SymbolOpt, (sym_1, sym_2, constant) = EnumSort('SymbolOpt', ('sym_1', 'sym_2', 'constant'))

num_regact = 2

RegActChoice, choices = EnumSort('RegActChoice', ['choose_%d' %i for i in range(num_regact)])


num_pred = 2
num_arith = 4

class Pred:
    def __init__(reg_act_id, pred_id, bitvecsize):
        self.reg_act_id = reg_act_id
        self.pred_id = pred_id
        self.op = Const('pred_op_%d_%d'%reg_act_id,pred_id, PredOp)
        self.const = BitVec('pred_const_%d_%d'%reg_act_id,pred_id, bitvecsize)
        self.sym_opt = Const('pred_sym_opt_%d_%d'%reg_act_id,pred_id, SymbolOpt)
        self.state_opt = Const('pred_state_opt_%d_%d'%reg_act_id,pred_id, StateOpt)

    def makePredCond(pre_state_1, pre_state_2, symbol_1, symbol_2, post_state_1, post_state_2):
        #Todo

class Arith:
    def __init__(reg_act_id, arith_id, bitvecsize):
        self.reg_act_id = reg_act_id
        self.pred_id = arith_id
        self.op = Const('arith_op_%d_%d'%reg_act_id,arith_id, ArithOp)
        self.sym_opt = Const('arith_sym_opt_%d_%d'%reg_act_id,arith_id, SymbolOpt)
        self.sym_const = BitVec('arith_sym_const_%d_%d'%reg_act_id,arith_id, bitvecsize)
        self.state_opt = Const('arith_state_opt_%d_%d'%reg_act_id,arith_id, StateOpt)
        self.state_const = BitVec('arith_state_const_%d_%d'%reg_act_id,arith_id, bitvecsize)
    
    def makeArithCond(pre_state_1, pre_state_2, symbol_1, symbol_2, post_state_1, post_state_2):
        #Todo

class RegAct:
    def __init__(reg_act_id, bitvecsize):
        self.reg_act_id = reg_act_id
        self.logicop = Const("logicop_%d" % reg_act_id, LogicOp)
        self.preds = [Pred(reg_act_id, i, bitvecsize) for i in range(num_pred)]
        self.ariths = [Arith(reg_act_id, i, bitvecsize) for i in range(num_arith)]
    
    def makeTransitionCond(pre_state_1, pre_state_2, symbol_1, symbol_2, post_state_1, post_state_2):
        #Todo
        

def createDFA(input, bitvecsize):
    constraints = []


    # per RegAct
    reg_acts = [RegAct(i, bitvecsize) for i in range(num_regact)]

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

        cond_regact=[]
        for i in range(num_regact):
            cond_pred = []
            for j in range(num_pred):
                pred_sym = If(list_pred_sym_opt[i][j] == SymbolOpt.sym_1, symbol_1, BitVecVal(0, bitvecsize)) + \
                             If(list_pred_sym_opt[i][j] == SymbolOpt.sym_2, symbol_2, BitVecVal(0, bitvecsize))
                pred_state = If(list_pred_state_opt[i][j] == StateOpt.state_1, pre_state_1, BitVecVal(0, bitvecsize)) + \
                               If(list_pred_state_opt[i][j] == StateOpt.state_2, pre_state_2, BitVecVal(0, bitvecsize))
                pred_arg = pred_state + pred_sym + list_pred_const[i][j]
                predicate_eq = If(list_predop[i][j] == PredOp.eq, pred_arg == BitVecVal(0, bitvecsize), False)
                predicate_ge = If(list_predop[i][j] == PredOp.ge, pred_arg >= BitVecVal(0, bitvecsize), False)
                predicate_le = If(list_predop[i][j] == PredOp.le, pred_arg <= BitVecVal(0, bitvecsize), False)
                predicate_neq = If(list_predop[i][j] == PredOp.neq, pred_arg != BitVecVal(0, bitvecsize), False)
                cond_pred.append(Or(predicate_eq, predicate_ge, predicate_le, predicate_neq))

            predicate_left = If(list_logicop[i] == LogicOp.left, cond_pred[0], False)
            predicate_right = If(list_logicop[i] == LogicOp.right, cond_pred[-1], False)
            predicate_and = If(list_logicop[i] == LogicOp.booland, And(cond_pred), False)
            predicate_or = If(list_logicop[i] == LogicOp.boolor, Or(cond_pred), False)
            predicate = Or(predicate_left, predicate_right, predicate_and, predicate_or)

            cond_arith = []
            for j in range(num_arith):
                arith_sym = If(list_arith_sym_opt[i][j] == SymbolOpt.sym_1, symbol_1, BitVecVal(0, bitvecsize)) + \
                            If(list_arith_sym_opt[i][j] == SymbolOpt.sym_2, symbol_2, BitVecVal(0, bitvecsize)) + \
                            If(list_arith_sym_opt[i][j] == SymbolOpt.constant, list_arith_sym_const[i][j], BitVecVal(0, bitvecsize))
                arith_state = If(list_arith_state_opt[i][j] == StateOpt.state_1, pre_state_1, BitVecVal(0, bitvecsize)) + \
                                If(list_arith_state_opt[i][j] == StateOpt.state_2, pre_state_2, BitVecVal(0, bitvecsize)) + \
                                If(list_arith_state_opt[i][j] == StateOpt.constant, list_arith_state_const[i][j], BitVecVal(0, bitvecsize))
                arithres_plus = If(list_arithop[i][j] == ArithOp.plus, arith_state + arith_sym, BitVecVal(0, bitvecsize))
                arithres_bxor = If(list_arithop[i][j] == ArithOp.bitxor, arith_state ^ arith_sym, BitVecVal(0, bitvecsize))
                arithres_band = If(list_arithop[i][j] == ArithOp.bitand, arith_state & arith_sym, BitVecVal(0, bitvecsize))
                arithres = arithres_plus + arithres_bxor + arithres_band
                cond_arith.append(arithres)
            
            branch_1 = And((post_state_1 == cond_arith[0]), (post_state_2 == cond_arith[2]))
            branch_2 = And((post_state_1 == cond_arith[1]), (post_state_2 == cond_arith[3]))

            cond_this_regact_sat = If(predicate, branch_1, branch_2)
            for i in range(num_regact):
                cond_regact.append(If(regact_id[transition[1]]==getattr(RegActChoice, "choose_%d" % i ),
                                   cond_this_regact_sat, False))

        constraints.append(Or(cond_regact))

    s = Solver()
    s.add(And(constraints))

    if (s.check() == unsat):
        print("unsat")
    else:
        print("sat, check output.txt")
        m = s.model()
        print(m)


def main():
    if (len(sys.argv) < 3):
        print ("please give input file and number of bits")
        quit()
    with open(sys.argv[1]) as file:
        input = json.load(file)
    bitvecsize = int(sys.argv[2])
    createDFA(input, bitvecsize)

if __name__ == '__main__':
    main()