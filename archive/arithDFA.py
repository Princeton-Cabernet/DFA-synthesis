from z3 import *
import json
import itertools

ArithOp, (plus, bitxor, bitand) = EnumSort('ArithOp', ('plus', 'bitxor', 'bitand'))
PredOp , (eq, ge, le, neq) = EnumSort('PredOp', ('eq', 'ge', 'le', 'neq'))

num_regact = 2

RegActChoice, choices = EnumSort('RegActChoice', ['choose_%d' %i for i in range(num_regact)])

def createDFA(input, bitvecsize):
    constraints = []

    # per RegAct
    
    list_predop = [Const('predop_%d' % i, PredOp) for i in range(num_regact)]
    list_predconst = [BitVec('predconst_%d' % i, bitvecsize) for i in range(num_regact)]
    list_pred_has_state = [Bool('pred_has_state_%d' % i) for i in range(num_regact)]
    list_pred_has_sval = [Bool('pred_has_sval_%d' % i) for i in range(num_regact)]

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
            predstate = If(list_pred_has_state[i], pre_state, BitVecVal(0, bitvecsize))
            predsval = If(list_pred_has_sval[i], symbol_pred, BitVecVal(0, bitvecsize))
            predarg = predstate + predsval + list_predconst[i]
            predicate_eq = If(list_predop[i] == PredOp.eq, predarg == BitVecVal(0, bitvecsize), False)
            predicate_ge = If(list_predop[i] == PredOp.ge, predarg >= BitVecVal(0, bitvecsize), False)
            predicate_le = If(list_predop[i] == PredOp.le, predarg <= BitVecVal(0, bitvecsize), False)
            predicate_neq = If(list_predop[i] == PredOp.neq, predarg != BitVecVal(0, bitvecsize), False)
            predicate = Or(predicate_eq, predicate_ge, predicate_le, predicate_neq)

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