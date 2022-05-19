from z3 import *
import json
import itertools

ArithOp, (plus, bitxor, bitand) = EnumSort('ArithOp', ('plus', 'bitxor', 'bitand'))
PredOp , (eq, ge, le, neq) = EnumSort('PredOp', ('eq', 'ge', 'le', 'neq'))

num_regact = 4

RegActChoice, choices = EnumSort('RegActChoice', ['choose_%d' %i for i in range(num_regact)])


def createDFA(input, bitvecsize):
    constraints = []
    # per RegAct
    # predop = Const('predop', PredOp)
    choice_predops = [Const('predop_%d'%i, PredOp) for i in range(num_regact)]
    
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
            predop = choice_predops[i]
            predicate_eq = If(predop == eq, pre_state == symbol_pred, False)
            predicate_ge = If(predop == ge, pre_state >= symbol_pred, False)
            predicate_le = If(predop == le, pre_state <= symbol_pred, False)
            predicate_neq = If(predop == neq, pre_state != symbol_pred, False)
            branch_changed = (post_state == symbol_val)
            branch_unchanged = (post_state == pre_state)
            predicate = Or(predicate_eq, predicate_ge, predicate_le, predicate_neq)
            cond_this_regact_sat = If(predicate , branch_changed, branch_unchanged)
            cond_regact.append(If(regact_id[transition[1]]==choices[i], cond_this_regact_sat, False))
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