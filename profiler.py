import sys
import json
import itertools
from genDFA import *
from line_profiler import LineProfiler
profile = LineProfiler()


from z3 import *
import json
import itertools

ArithOp = Datatype('ArithOp')
ArithOp.declare('plus')
ArithOp.declare('bitxor')
ArithOp.declare('bitand')
ArithOp = ArithOp.create()

PredOp = Datatype('PredOp')
PredOp.declare('eq')
PredOp.declare('ge')
PredOp.declare('le')
PredOp.declare('neq')
PredOp = PredOp.create()

LogicOp = Datatype('LogicOp')
LogicOp.declare('left')
LogicOp.declare('right')
LogicOp.declare('booland')
LogicOp.declare('boolor')
LogicOp = LogicOp.create()

num_regact = 2

RegActChoice = Datatype('RegActChoice')
for i in range(num_regact):
    RegActChoice.declare('choose_%d' % i)
RegActChoice = RegActChoice.create()


@profile
def createDFA(input, bitvecsize):
    constraints = []

    # per RegAct
    list_logicop = [Const("logicop_%d" % i, LogicOp) for i in range(num_regact)]

    list_predop_1 = [Const('predop_1_%d' % i, PredOp) for i in range(num_regact)]
    list_predconst_1 = [BitVec('predconst_1_%d' % i, bitvecsize) for i in range(num_regact)]
    list_pred_has_state_1 = [Bool('pred_has_state_1_%d' % i) for i in range(num_regact)]
    list_pred_has_sval_1 = [Bool('pred_has_sval_1_%d' % i) for i in range(num_regact)]

    list_predop_2 = [Const('predop_2_%d' % i, PredOp) for i in range(num_regact)]
    list_predconst_2 = [BitVec('predconst_2_%d' % i, bitvecsize) for i in range(num_regact)]
    list_pred_has_state_2 = [Bool('pred_has_state_2_%d' % i) for i in range(num_regact)]
    list_pred_has_sval_2 = [Bool('pred_has_sval_2_%d' % i) for i in range(num_regact)]

    list_arithop_1 = [Const('arithop_1_%d' % i, ArithOp) for i in range(num_regact)]
    list_aritharg_const_1 = [BitVec('aritharg_const_1_%d' % i, bitvecsize) for i in range(num_regact)]
    list_arithstate_const_1 = [BitVec('arithstate_const_1_%d' % i, bitvecsize) for i in range(num_regact)]
    list_aritharg_is_const_1 = [Bool('aritharg_is_const_1_%d' % i) for i in range(num_regact)]
    list_arithstate_is_const_1 = [Bool('arithstate_is_const_1_%d' % i) for i in range(num_regact)]

    list_arithop_2 = [Const('arithop_2_%d' % i, ArithOp) for i in range(num_regact)]
    list_aritharg_const_2 = [BitVec('aritharg_const_2_%d' % i, bitvecsize) for i in range(num_regact)]
    list_arithstate_const_2 = [BitVec('arithstate_const_2_%d' % i, bitvecsize) for i in range(num_regact)]
    list_aritharg_is_const_2 = [Bool('aritharg_is_const_2_%d' % i) for i in range(num_regact)]
    list_arithstate_is_const_2 = [Bool('arithstate_is_const_2_%d' % i) for i in range(num_regact)]

    # per symbol
    symbols_pred = {}
    symbols_val = {}
    regact_id = {}

    for symbol in input["sigma"]:
        symbols_pred[symbol] = BitVec("pred_%s" % symbol, bitvecsize)
        symbols_val[symbol] = BitVec("val_%s" % symbol, bitvecsize)
        regact_id[symbol] = Const("regact_%s" % symbol, RegActChoice)

    # per state
    states = {}
    for state in input["states"]:
        states[state] = BitVec("state_%s" % state, bitvecsize)
    constraints.append(states[input["initial"]] == BitVecVal(0, bitvecsize))
    for s1, s2 in itertools.product(states.keys(), states.keys()):
        if s1 != s2: constraints.append(states[s1] != states[s2])

    #per transition
    for transition in input["transitions"]:
        pre_state = states[transition[0]]
        symbol_pred = symbols_pred[transition[1]]
        symbol_val = symbols_val[transition[1]]
        post_state = states[transition[2]]

        cond_regact=[]
        for i in range(num_regact):
            predstate_1 = If(list_pred_has_state_1[i], pre_state, BitVecVal(0, bitvecsize))
            predsval_1 = If(list_pred_has_sval_1[i], symbol_pred, BitVecVal(0, bitvecsize))
            predarg_1 = predstate_1 + predsval_1 + list_predconst_1[i]
            predicate_eq_1 = If(list_predop_1[i] == PredOp.eq, predarg_1 == BitVecVal(0, bitvecsize), False)
            predicate_ge_1 = If(list_predop_1[i] == PredOp.ge, predarg_1 >= BitVecVal(0, bitvecsize), False)
            predicate_le_1 = If(list_predop_1[i] == PredOp.le, predarg_1 <= BitVecVal(0, bitvecsize), False)
            predicate_neq_1 = If(list_predop_1[i] == PredOp.neq, predarg_1 != BitVecVal(0, bitvecsize), False)
            predicate_1 = Or(predicate_eq_1, predicate_ge_1, predicate_le_1, predicate_neq_1)

            predstate_2 = If(list_pred_has_state_2[i], pre_state, BitVecVal(0, bitvecsize))
            predsval_2 = If(list_pred_has_sval_2[i], symbol_pred, BitVecVal(0, bitvecsize))
            predarg_2 = predstate_2 + predsval_2 + list_predconst_2[i]
            predicate_eq_2 = If(list_predop_2[i] == PredOp.eq, predarg_2 == BitVecVal(0, bitvecsize), False)
            predicate_ge_2 = If(list_predop_2[i] == PredOp.ge, predarg_2 >= BitVecVal(0, bitvecsize), False)
            predicate_le_2 = If(list_predop_2[i] == PredOp.le, predarg_2 <= BitVecVal(0, bitvecsize), False)
            predicate_neq_2 = If(list_predop_2[i] == PredOp.neq, predarg_2 != BitVecVal(0, bitvecsize), False)
            predicate_2 = Or(predicate_eq_2, predicate_ge_2, predicate_le_2, predicate_neq_2)

            predicate_left = If(list_logicop[i] == LogicOp.left, predicate_1, False)
            predicate_right = If(list_logicop[i] == LogicOp.right, predicate_2, False)
            predicate_and = If(list_logicop[i] == LogicOp.booland, And(predicate_1, predicate_2), False)
            predicate_or = If(list_logicop[i] == LogicOp.boolor, Or(predicate_1, predicate_2), False)
            predicate = Or(predicate_left, predicate_right, predicate_and, predicate_or)

            aritharg_1 = If(list_aritharg_is_const_1[i], list_aritharg_const_1[i], symbol_val)
            arithstate_1 = If(list_arithstate_is_const_1[i], list_arithstate_const_1[i], pre_state)
            arithres_plus_1 = If(list_arithop_1[i] == ArithOp.plus, arithstate_1 + aritharg_1, BitVecVal(0, bitvecsize))
            arithres_bxor_1 = If(list_arithop_1[i] == ArithOp.bitxor, arithstate_1 ^ aritharg_1, BitVecVal(0, bitvecsize))
            arithres_band_1 = If(list_arithop_1[i] == ArithOp.bitand, arithstate_1 & aritharg_1, BitVecVal(0, bitvecsize))
            arithres_1 = arithres_plus_1 + arithres_bxor_1 + arithres_band_1
            branch_1 = (post_state == arithres_1)

            aritharg_2 = If(list_aritharg_is_const_2[i], list_aritharg_const_2[i], symbol_val)
            arithstate_2 = If(list_arithstate_is_const_2[i], list_arithstate_const_2[i], pre_state)
            arithres_plus_2 = If(list_arithop_2[i] == ArithOp.plus, arithstate_2 + aritharg_2, BitVecVal(0, bitvecsize))
            arithres_bxor_2 = If(list_arithop_2[i] == ArithOp.bitxor, arithstate_2 ^ aritharg_2, BitVecVal(0, bitvecsize))
            arithres_band_2 = If(list_arithop_2[i] == ArithOp.bitand, arithstate_2 & aritharg_2, BitVecVal(0, bitvecsize))
            arithres_2 = arithres_plus_2 + arithres_bxor_2 + arithres_band_2
            branch_2 = (post_state == arithres_2)

            cond_this_regact_sat = If(predicate, branch_1, branch_2)
            for i in range(num_regact):
                cond_regact.append(If(regact_id[transition[1]]==getattr(RegActChoice, "choose_%d" % i ),
                                   cond_this_regact_sat, False))

        constraints.append(Or(cond_regact))

    s = Solver()
    s.add(And(constraints))
    s.set("timeout", 1 * 1000)
    if s.check() == sat:
        print("sat, check output.txt")
        m = s.model()
        print(m)
    else:
        print("unsat")


if __name__ == '__main__':
    arith_bin = True
    two_cond = True
    four_branch = False
    bitvecsize = 8
    timeout = 1

    file = "s4.json"
    two_slot = False
    path = "examples/%s" % file
    sys.stderr.write("Parameters: two_slot: %s, file: %s, num_regact: %d\n" % (two_slot, file, num_regact))
    input_json=json.load(open(path))
    createDFA(input_json, bitvecsize)
    
    profile.print_stats()
