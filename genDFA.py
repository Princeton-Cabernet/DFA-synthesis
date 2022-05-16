from z3 import *
import json
import itertools

# Enum sorts
ArithOp, (plus, bitxor, bitand) = EnumSort('ArithOp', ('plus', 'bitxor', 'bitand'))
PredOp , (eq, ge, le, neq) = EnumSort('PredOp', ('eq', 'ge', 'le', 'neq'))
LogicOp, (left, right, booland, boolor) = EnumSort('LogicOp', ('left', 'right', 'booland', 'boolor'))
StateOpt, (state_1, state_2, stateconstant) = EnumSort('StateOpt', ('state_1', 'state_2', 'stateconstant')) 
SymbolOpt, (sym_1, sym_2, symconstant) = EnumSort('SymbolOpt', ('sym_1', 'sym_2', 'symconstant'))

# Tunable parameters
arith_bin = True
two_cond = True
two_slot = True
four_branch = False
# assertion when four_branch == True: two_slot == True, two_cond == True
assert(two_slot and two_cond if four_branch else True)
num_regact = 4
bitvecsize = 4

# Classic cases:
# TwoTernary: {arith_bin = True, two_cond = True, two_slot = True, four_branch = True}
# TwoSlot: {arith_bin = True, two_cond = True, two_slot = True, four_branch = False}
# TwoCond: {arith_bin = True, two_cond = True, two_slot = False, four_branch = False}
# Arith: {arith_bin = True, two_cond = False, two_slot = False, four_branch = False}
# Simple: {arith_bin = False, two_cond = False, two_slot = False, four_branch = False}

# Regact choice sort
RegActChoice, choices = EnumSort('RegActChoice', ['choose_%d' %i for i in range(num_regact)])
# constant zero
zero = BitVecVal(0, bitvecsize)

def access(model, val):
    return model[val].as_long() if (model[val] != None) else None

class Pred:
    def __init__(self, regact_id, pred_id):
        self.regact_id = regact_id
        self.pred_id = pred_id
        self.op = Const('pred_op_%d_%d' % (regact_id, pred_id), PredOp)
        self.const = BitVec('pred_const_%d_%d' % (regact_id, pred_id), bitvecsize)
        self.sym_opt = Const('pred_sym_opt_%d_%d' % (regact_id, pred_id), SymbolOpt)
        self.state_opt = Const('pred_state_opt_%d_%d' % (regact_id, pred_id), StateOpt)

    def makeDFACond(self):
        constraints = []
        if not arith_bin:
            constraints.append(Or(self.sym_opt == symconstant, self.state_opt == stateconstant))
        if not two_slot:
            constraints.append(self.state_opt != state_2)
        return constraints

    def makePredCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        pred_sym = If(self.sym_opt == sym_1, symbol_1, 
                   If(self.sym_opt == sym_2, symbol_2, 
                   If(self.sym_opt == symconstant, zero, zero)))
        pred_state = If(self.state_opt == state_1, pre_state_1, 
                     If(self.state_opt == state_2, pre_state_2, 
                     If(self.state_opt == stateconstant, zero, zero)))
        pred_arg = pred_state + pred_sym + self.const
        predicate_eq = If(self.op == eq, pred_arg == zero, True)
        predicate_ge = If(self.op == ge, pred_arg >= zero, True)
        predicate_le = If(self.op == le, pred_arg <= zero, True)
        predicate_neq = If(self.op == neq, pred_arg != zero, True)
        return And(predicate_eq, predicate_ge, predicate_le, predicate_neq)

    def toJSON(self, model):
        config = { "op": str(model[self.op]),
                   "const": access(model, self.const),
                   "sym_opt": str(model[self.sym_opt]),
                   "state_opt": str(model[self.state_opt]) }
        return config

class Arith:
    def __init__(self, regact_id, arith_id):
        self.regact_id = regact_id
        self.arith_id = arith_id
        self.op = Const('arith_op_%d_%d'% (regact_id, arith_id), ArithOp)
        self.sym_opt = Const('arith_sym_opt_%d_%d'% (regact_id, arith_id), SymbolOpt)
        self.sym_const = BitVec('arith_sym_const_%d_%d'% (regact_id, arith_id), bitvecsize)
        self.state_opt = Const('arith_state_opt_%d_%d'% (regact_id, arith_id), StateOpt)
        self.state_const = BitVec('arith_state_const_%d_%d'% (regact_id, arith_id), bitvecsize)
    
    def makeDFACond(self):
        constraints = []
        if not arith_bin:
            constraints.append(And(Or(And(self.sym_opt == symconstant, self.sym_const == zero), 
                               And(self.state_opt == stateconstant, self.state_const == zero)),
                        self.op == bitxor))
        if not two_slot:
            constraints.append(self.state_opt != state_2)
        return constraints

    def makeArithCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        arith_sym = If(self.sym_opt == sym_1, symbol_1, 
                    If(self.sym_opt == sym_2, symbol_2, 
                    If(self.sym_opt == symconstant, self.sym_const, zero)))
        arith_state = If(self.state_opt == state_1, pre_state_1, 
                      If(self.state_opt == state_2, pre_state_2, 
                      If(self.state_opt == stateconstant, self.state_const, zero)))
        arith_res = If(self.op == plus, arith_state + arith_sym, 
                   If(self.op == bitxor, arith_state ^ arith_sym, 
                   If(self.op == bitand, arith_state & arith_sym, zero)))
        return arith_res

    def toJSON(self, model):
        config = { "op": str(model[self.op]),
                   "sym_opt": str(model[self.sym_opt]),
                   "sym_const": access(model, self.sym_const),
                   "state_opt": str(model[self.state_opt]),
                   "state_const": access(model, self.state_const) }
        return config

class RegAct:
    def __init__(self, regact_id):
        self.num_pred = 2 if two_cond else 1
        self.num_arith = 4 if two_slot else 2
        self.num_logical_op = 2 if four_branch else 1
        self.regact_id = regact_id
        self.preds = [Pred(regact_id, i) for i in range(self.num_pred)]
        self.ariths = [Arith(regact_id, i) for i in range(self.num_arith)]
        self.logic_ops = [Const("logic_op_%d_%d" % (regact_id, i), LogicOp) for i in range(self.num_logical_op)]
        self.state_1_is_main = Bool("state_1_is_main_%d" % regact_id)
    
    def makeDFACond(self):
        constraints = []
        cp = [p.makeDFACond() for p in self.preds]
        constraints.extend(itertools.chain.from_iterable(cp))
        ca = [a.makeDFACond() for a in self.ariths]
        constraints.extend(itertools.chain.from_iterable(ca))
        if not two_cond:
            constraints.append(self.logic_ops[0] == left)
        if not two_slot:
            constraints.append(self.state_1_is_main)
        return constraints

    def makeTransitionCond(self, pre_state_1, pre_state_2, symbol_1, symbol_2, post_state_1, post_state_2, post_state_1_is_main):
        pred_conds= [p.makePredCond(pre_state_1, pre_state_2, symbol_1, symbol_2) for p in self.preds]
        arith_exprs= [a.makeArithCond(pre_state_1, pre_state_2, symbol_1, symbol_2) for a in self.ariths]
        if two_cond:
            pred_combos = [If(self.logic_ops[i] == left, pred_conds[0], 
                           If(self.logic_ops[i] == right, pred_conds[1], 
                           If(self.logic_ops[i] == booland, And(pred_conds[0], pred_conds[1]), 
                           If(self.logic_ops[i] == boolor, Or(pred_conds[0], pred_conds[1]), False))))
                           for i in range(self.num_logical_op)]
        else:
            pred_combos = [pred_conds[0]]
        constraints= []
        if two_slot:
            if four_branch:
                constraints.append(If(pred_combos[0], post_state_1 == arith_exprs[0], post_state_1 == arith_exprs[2]))
                constraints.append(If(pred_combos[1], post_state_2 == arith_exprs[1], post_state_2 == arith_exprs[3]))
            else:
                branch_true = And(post_state_1 == arith_exprs[0], post_state_2 == arith_exprs[1])
                branch_false = And(post_state_1 == arith_exprs[2], post_state_2 == arith_exprs[3])
                constraints.append(If(pred_combos[0], branch_true, branch_false))
        else:
            branch_true = And(post_state_1 == arith_exprs[0])
            branch_false = And(post_state_1 == arith_exprs[1])
            constraints.append(If(pred_combos[0], branch_true, branch_false))
        constraints.append(self.state_1_is_main == post_state_1_is_main)
        return And(constraints)

    def toJSON(self, model):
        config = { "logic_ops" : [str(model[op]) for op in self.logic_ops], 
                   "preds" : [p.toJSON(model) for p in self.preds], 
                   "ariths" : [a.toJSON(model) for a in self.ariths],
                   "state_1_is_main" : bool(model[self.state_1_is_main]) }
        return config

def toJSON(model, symbols_1, symbols_2, regact_id, states_1, states_2, states_1_is_main, regacts):
    config = {}
    config["bitvecsize"] = bitvecsize
    config["symbols_1"] = { sym : access(model, val) for sym, val in symbols_1.items() }
    config["symbols_2"] = { sym : access(model, val) for sym, val in symbols_2.items() }
    config["regact_id"] = { sym : (int(str(model[val]).split('_')[1]) if val != None else None)
                            for sym, val in regact_id.items() }
    config["states_1"] = { state : access(model, val) for state, val in states_1.items() }
    if two_slot:
        config["states_2"] = { state : access(model, val) for state, val in states_2.items() }
        config["states_1_is_main"] = { state : bool(model[val]) for state, val in states_1_is_main.items() }
    config["regacts"] = [r.toJSON(model) for r in regacts]
    return config

def createDFA(input, output):
    # constraints
    constraints = []

    # per RegAct
    regacts = [RegAct(i) for i in range(num_regact)]
    for regact in regacts:
        constraints.extend(regact.makeDFACond())

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
            post_state_1_is_main = states_1_is_main[transition[2]]

            s.add(If(regact_id[transition[1]] == choices[reg_adding], 
                     regacts[reg_adding].makeTransitionCond(pre_state_1, pre_state_2, symbol_1, symbol_2, 
                                                             post_state_1, post_state_2, post_state_1_is_main), 
                     True))
            s.push()
            for symbol in input["sigma"]:
                choice_constraints = []
                for i in range(reg_adding + 1):
                    choice_constraints.append(regact_id[symbol] == choices[i])
                s.add(Or(choice_constraints))
        if s.check() == sat:
            print("Sat with %d regacts." % (reg_adding + 1))
            model = s.model()
            config = toJSON(model, symbols_1, symbols_2, regact_id, 
                            states_1, states_2, states_1_is_main, regacts[: reg_adding + 1])
            print(json.dumps(config))
            with open(output, 'w') as file:
                json.dump(config, file)
            break
        elif reg_adding >= num_regact - 1:
            print("Unsat.")
            break
        else:
            s.pop()
            reg_adding += 1

def main():
    if (len(sys.argv) < 3):
        print ("please give input file and output config name")
        quit()
    with open(sys.argv[1]) as file:
        input = json.load(file)
    output = sys.argv[2]
    createDFA(input, output)

if __name__ == '__main__':
    main()