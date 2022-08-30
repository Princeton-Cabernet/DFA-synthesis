import sys
import json
import argparse
import warnings
import traceback
import re

bitvecsize = 0

def access(dict, dft_val = 0):
    return {key: dict[key] if (dict[key] != None) else dft_val for key in dict.keys()}

def sign(val, num_bits):
    max_int = 1 << (num_bits - 1)
    bound = max_int << 1
    masked_val = val & (bound - 1)
    return masked_val if masked_val < max_int else masked_val - bound

def unsign(val, num_bits):
    bound = 1 << num_bits
    return val & (bound - 1)

class Pred:
    def __init__(self, op, const, sym_opt, state_opt, warning):
        self.op = op
        self.const = const
        self.sym_opt = sym_opt
        self.state_opt = state_opt
        self.warning = warning

    def to_p4_stmt(self, namespace='dfa_'):
        if self.sym_opt == "s1":
            pred_sym = namespace+'symbol_1'
        elif self.sym_opt == "s2":
            pred_sym = namespace+'symbol_2'
        elif self.sym_opt == "const":
            pred_sym = '0'
        else:
            if self.warning:
                warnings.warn("Null in predicate sym.")
            pred_sym = '0'
        if self.state_opt == "s1":
            pred_state = 'in_value.lo'
        elif self.state_opt == "s2":
            pred_state = 'in_value.hi'
        elif self.state_opt == "const":
            pred_state = '0'
        else:
            if self.warning:
                warnings.warn("Null in predicate state.")
            pred_state = '0'
        pred_const = '0' if self.const == None else str(self.const)
        global bitvecsize
        if self.op == "eq":
            op_str='=='
        elif self.op == "ge":
            op_str='>='
        elif self.op == "le":
            op_str='<='
        elif self.op == "neq":
            op_str='!='
        casted_pred_const=-int(pred_const)
        return f'({pred_state} + {pred_sym} {op_str} {casted_pred_const})'

    def execute(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        if self.sym_opt == "s1":
            pred_sym = symbol_1
        elif self.sym_opt == "s2":
            pred_sym = symbol_2
        elif self.sym_opt == "const":
            pred_sym = 0
        else:
            if self.warning:
                warnings.warn("Null in predicate sym.")
            pred_sym = 0
        if self.state_opt == "s1":
            pred_state = pre_state_1
        elif self.state_opt == "s2":
            pred_state = pre_state_2
        elif self.state_opt == "const":
            pred_state = 0
        else:
            if self.warning:
                warnings.warn("Null in predicate state.")
            pred_state = 0
        pred_const = 0 if self.const == None else self.const
        global bitvecsize
        pred_arg = sign(pred_state + pred_sym + pred_const, bitvecsize)
        if self.op == "eq":
            return pred_arg == 0
        elif self.op == "ge":
            return pred_arg >= 0
        elif self.op == "le":
            return pred_arg <= 0
        elif self.op == "neq":
            return pred_arg != 0
        else:
            warnings.warn("Null in predicate operator.")
            return pred_arg == 0

class Arith:
    def __init__(self, op, sym_opt, sym_const, state_opt, state_const, warning):
        self.op = op
        self.sym_opt = sym_opt
        self.sym_const = sym_const
        self.state_opt = state_opt
        self.state_const = state_const
        self.warning = warning
    
    def to_p4_stmt(self, namespace='dfa_'):
        if self.sym_opt == "s1":
            arith_sym = namespace+'symbol_1'
        elif self.sym_opt == "s2":
            arith_sym = namespace+'symbol_2'
        elif self.sym_opt == "const":
            if self.sym_const != None:
                arith_sym = str(self.sym_const)
            else:
                if self.warning:
                    warnings.warn("Null in arithmetic symbol constant.")
                arith_sym = '0'
        else:
            if self.warning:
                warnings.warn("Null in arithmetic symbol.")
            arith_sym = '0'
        if self.state_opt == "s1":
            arith_state = 'in_value.lo'
        elif self.state_opt == "s2":
            arith_state = 'in_value.hi'
        elif self.state_opt == "const":
            if self.state_const != None:
                arith_state = str(self.state_const)
            else:
                if self.warning:
                    warnings.warn("Null in arithmetic symbol constant.")
                arith_state = '0'
        else:
            if self.warning:
                warnings.warn("Null in arithmetic state.")
            arith_state = '0'
        if self.op == "plus":
            arith_res = f'({arith_sym} + {arith_state})'
        elif self.op == "xor":
            arith_res =  f'({arith_sym} ^ {arith_state})'
        elif self.op == "and":
            arith_res =  f'({arith_sym} & {arith_state})'
        elif self.op == "or":
            arith_res =  f'({arith_sym} | {arith_state})'
        elif self.op == "sub":
            arith_res =  f'({arith_sym} - {arith_state})'
        elif self.op == "subr":
            arith_res = f'({arith_state} - {arith_sym})'
        elif self.op == "nand":
            arith_res = f'(~({arith_sym} & {arith_state}))'
        elif self.op == "andca":
            arith_res =  f'((~ {arith_sym}) & {arith_state})'
        elif self.op == "andcb":
            arith_res =  f'({arith_sym} & (~ {arith_state}))'
        elif self.op == "nor":
            arith_res =  f'(~ ({arith_sym} | {arith_state}))'
        elif self.op == "orca":
            arith_res =  f'((~ {arith_sym}) | {arith_state})'
        elif self.op == "orcb":
            arith_res =  f'({arith_sym} | (~ {arith_state}))'
        elif self.op == "xnor":
            arith_res =  f'(~ ({arith_sym} ^ {arith_state}))'
        else:
            if self.warning:
                warnings.warn("Null in arithmetic operator.")
            arith_res =  f'({arith_sym} + {arith_state})'
        return arith_res

    def execute(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        if self.sym_opt == "s1":
            arith_sym = symbol_1
        elif self.sym_opt == "s2":
            arith_sym = symbol_2
        elif self.sym_opt == "const":
            if self.sym_const != None:
                arith_sym = self.sym_const
            else:
                if self.warning:
                    warnings.warn("Null in arithmetic symbol constant.")
                arith_sym = 0
        else:
            if self.warning:
                warnings.warn("Null in arithmetic symbol.")
            arith_sym = 0
        if self.state_opt == "s1":
            arith_state = pre_state_1
        elif self.state_opt == "s2":
            arith_state = pre_state_2
        elif self.state_opt == "const":
            if self.state_const != None:
                arith_state = self.state_const
            else:
                if self.warning:
                    warnings.warn("Null in arithmetic symbol constant.")
                arith_state = 0
        else:
            if self.warning:
                warnings.warn("Null in arithmetic state.")
            arith_state = 0
        if self.op == "plus":
            arith_res = arith_sym + arith_state
        elif self.op == "xor":
            arith_res =  arith_sym ^ arith_state
        elif self.op == "and":
            arith_res =  arith_sym & arith_state
        elif self.op == "or":
            arith_res =  arith_sym | arith_state
        elif self.op == "sub":
            arith_res =  arith_sym - arith_state
        elif self.op == "subr":
            arith_res = arith_state - arith_sym
        elif self.op == "nand":
            arith_res =  ~ (arith_sym & arith_state)
        elif self.op == "andca":
            arith_res =  (~ arith_sym) & arith_state
        elif self.op == "andcb":
            arith_res =  arith_sym & (~ arith_state)
        elif self.op == "nor":
            arith_res =  ~ (arith_sym | arith_state)
        elif self.op == "orca":
            arith_res =  (~ arith_sym) | arith_state
        elif self.op == "orcb":
            arith_res =  arith_sym | (~ arith_state)
        elif self.op == "xnor":
            arith_res =  ~ (arith_sym ^ arith_state)
        else:
            if self.warning:
                warnings.warn("Null in arithmetic operator.")
            arith_res =  arith_sym + arith_state
        return unsign(arith_res, bitvecsize)

class RegAct:
    def __init__(self, preds, ariths, logic_ops, state_1_is_main, warning):
        self.preds = [Pred(warning=warning, **p) for p in preds]
        self.ariths = [Arith(warning=warning, **a) for a in ariths]
        self.logic_ops = logic_ops
        self.state_1_is_main = state_1_is_main if state_1_is_main != None else True
        self.warning = warning

    def to_p4_code(self, namespace, reg_name, regact_name):
        template=f'''
        RegisterAction<paired_{bitvecsize}bit, _, bit<{bitvecsize}>>({reg_name}) {regact_name}= {{  
            void apply(inout paired_{bitvecsize}bit value, out bit<{bitvecsize}> rv) {{          
                rv = 0;                                                    
                paired_{bitvecsize}bit in_value;                                   
                in_value = value;                 
                
                %PRED_DEFN%

                %COND_BRANCH%

                %RETURN_STMT%
            }}                                                              
        }};
        '''
        PRED_DEFN='';
        for i,pred in enumerate(self.preds):
            stmt=f'bool pred_{i}=' + pred.to_p4_stmt(namespace) +';'
            PRED_DEFN+=stmt+'\n'
        template=template.replace('%PRED_DEFN%',PRED_DEFN)

        pred_combos_stmt=[]
        for i in range(len(self.logic_ops)):
            if self.logic_ops[i] == "left":
                pred_combos_stmt.append('pred_0')
            elif self.logic_ops[i] == "right":
                pred_combos_stmt.append('pred_1')
            elif self.logic_ops[i] == "and":
                pred_combos_stmt.append('pred_0 && pred_1')
            elif self.logic_ops[i] == "or":
                pred_combos_stmt.append('pred_0 || pred_1')
                pred_combos_stmt.append('pred_0 || pred_1')
            else:
                if self.warning:
                    warnings.warn("Null in logical operator.")
                pred_combos_stmt.append('pred_0')
        
        arith_stmts=[a.to_p4_stmt(namespace) for a in self.ariths]
        if len(self.ariths) == 4:
            if len(self.logic_ops) == 2:
                # if self.warning:
                #     warnings.warn("Tofino Compiler might not like the four-branch code we generate. Need to use nested if-s.")
                # COND_BRANCH=f"""
                # if({pred_combos_stmt[0]}){{
                #     value.lo={arith_stmts[0]};
                # }}else{{
                #     value.lo={arith_stmts[1]};
                # }}
                # if({pred_combos_stmt[1]}){{
                #     value.hi={arith_stmts[2]};
                # }}else{{
                #     value.hi={arith_stmts[3]};
                # }}
                # """ 
                COND_BRANCH=f"""
                if({pred_combos_stmt[0]}){{
                    if({pred_combos_stmt[1]}){{
                        value.lo={arith_stmts[0]};
                        value.hi={arith_stmts[2]};
                    }}else{{
                        value.lo={arith_stmts[0]};
                        value.hi={arith_stmts[3]};
                    }}
                }}else{{
                    if({pred_combos_stmt[1]}){{
                        value.lo={arith_stmts[1]};
                        value.hi={arith_stmts[2]};
                    }}else{{
                        value.lo={arith_stmts[1]};
                        value.hi={arith_stmts[3]};
                    }}
                }}
                """                    
            else:
                COND_BRANCH=f"""
                if({pred_combos_stmt[0]}){{
                    value.lo={arith_stmts[0]};
                    value.hi={arith_stmts[2]};
                }}else{{
                    value.lo={arith_stmts[1]};
                    value.hi={arith_stmts[3]};
                }}
                """
        else:
            COND_BRANCH=f"""
            if({pred_combos_stmt[0]}){{
                value.lo={arith_stmts[0]};
            }}else{{
                value.lo={arith_stmts[1]};
            }}
            //value.hi=0; //pair mode not used (post_state_2 = None)
            """
        template=template.replace('%COND_BRANCH%',COND_BRANCH)

        if self.state_1_is_main:
            RETURN_STMT='rv=value.lo;'
        else:
            RETURN_STMT='rv=value.hi;'
        template=template.replace('%RETURN_STMT%',RETURN_STMT)

        return template;

    def execute(self, pre_state_1, pre_state_2, symbol_1, symbol_2):
        pred_conds = [p.execute(pre_state_1, pre_state_2, symbol_1, symbol_2) for p in self.preds]
        arith_exprs = [a.execute(pre_state_1, pre_state_2, symbol_1, symbol_2) for a in self.ariths]
        pred_combos = []
        for i in range(len(self.logic_ops)):
            if self.logic_ops[i] == "left":
                pred_combos.append(pred_conds[0])
            elif self.logic_ops[i] == "right":
                pred_combos.append(pred_conds[1])
            elif self.logic_ops[i] == "and":
                pred_combos.append(pred_conds[0] & pred_conds[1])
            elif self.logic_ops[i] == "or":
                pred_combos.append(pred_conds[0] | pred_conds[1])
            else:
                if self.warning:
                    warnings.warn("Null in logical operator.")
                pred_combos.append(pred_conds[0])
        post_state_2 = None
        if len(self.ariths) == 4:
            if len(self.logic_ops) == 2:
                post_state_1 = arith_exprs[0] if pred_combos[0] else arith_exprs[2]
                post_state_2 = arith_exprs[1] if pred_combos[1] else arith_exprs[3]
            else:
                post_state_1 = arith_exprs[0] if pred_combos[0] else arith_exprs[2]
                post_state_2 = arith_exprs[1] if pred_combos[0] else arith_exprs[3]
        else:
            post_state_1 = arith_exprs[0] if pred_combos[0] else arith_exprs[1]
        return post_state_1, post_state_2, self.state_1_is_main

def string_to_pair(s):
    return tuple(s.rsplit('_', 1))

def generateP4(input, config, warning, namespace='dfa_', reg_name='reg_DFA', reg_size=1024):
    global bitvecsize
    bitvecsize = config["bitvecsize"]
    symbols_1 = access(config["symbols_1"])
    symbols_2 = access(config["symbols_2"])
    regact_id = access(config["regact_id"])
    states_1 = access(config["states_1"])
    states_1 = {string_to_pair(k) : v for k, v in states_1.items()}

    if "states_2" in config :
        states_2 = access(config["states_2"])
        states_2 = {string_to_pair(k) : v for k, v in states_2.items()}
        if "states_1_is_main" in config:
            states_1_is_main = {string_to_pair(k) : v for k, v in config["states_1_is_main"].items()}
            back_to_state = {(states_1[k] if v else states_2[k]) : k[0] for k, v in states_1_is_main.items()}
        else:
            states_1_is_main = None
            back_to_state = {v : k[0] for k, v in states_1.items()}
        states_2 = {state : [v for k, v in sorted(states_2.items(), key=lambda kv:kv[0][1]) if state == k[0]] for state in input["states"]}
    else:
        states_2 = None
        states_1_is_main = None
        back_to_state = {v : k[0] for k, v in states_1.items()}

    states_1 = {state : [v for k, v in sorted(states_1.items(), key=lambda kv:kv[0][1]) if state == k[0]] for state in input["states"]}

    for r in config["regacts"]:
        if "state_1_is_main" not in r: r["state_1_is_main"] = True
    regacts = [RegAct(warning=warning, **r) for r in config["regacts"]]


    struct_definitions=f"""
    #IFNDEF PAIRED_{bitvecsize}BIT
    #DEFINE PAIRED_{bitvecsize}BIT
        struct paired_{bitvecsize}bit {{
            bit<{bitvecsize}> lo;
            bit<{bitvecsize}> hi;
        }}
    #ENDIF
    """

    definitions=f"""
    bit<{bitvecsize}> {namespace}_SYMBOL;
    bit<{bitvecsize}> {namespace}symbol_1;
    bit<{bitvecsize}> {namespace}symbol_2;
    bit<{bitvecsize}> {namespace}rv;

    Register<paired_{bitvecsize}bit,_>({reg_size}) {reg_name};
    bit<16> {namespace}reg_index=0;
    """
    for i,sym in enumerate(input['sigma']):
        definitions+=f"\nconst bit<{bitvecsize}> {namespace}_SYMBOLID_{sym}={i};\n"

    for i,sym in enumerate(input['sigma']):
        symbol_1 = symbols_1[sym]
        symbol_2 = symbols_1[sym]
        definitions+=f"""
        action {namespace}assign_symbol_{sym}(){{
            {namespace}_SYMBOL = {i};
            {namespace}symbol_1 = {symbol_1};
            {namespace}symbol_2 = {symbol_2};
        }}
        """
    for state in input['states']:
        definitions+=f"""
        action {namespace}process_state_{state}(){{
            //@action={state} TODO customized post-processing logic given new state {state}
        }}
        """


    list_pre_actions='\n\t\t'.join([f'{namespace}assign_symbol_{sym};' for sym in input['sigma']])
    
    list_post_actions='\n\t\t'.join([f'{namespace}process_state_{state};' for state in input['states']])
    list_post_entries='\n\t\t'.join([
            f'({num}): {namespace}process_state_{state}();'
            for num,state in back_to_state.items()
        ])
    table_1=f"""
        table tb_map_packet_to_symbol{{
            key = {{
                //@keys TODO use customize keys and match-action rules 
            }}
            actions = {{
                {list_pre_actions}
            }}
        }}
        //@index={namespace}reg_index TODO assign the right memory index to 
    """
    table_3=f"""
        table tb_map_rv_to_state{{
            key = {{
                {namespace}rv: exact;
            }}
            actions = {{
                {list_post_actions}
            }}
            const entries = {{
                {list_post_entries}
            }}
        }}
    """

    for i,RA in enumerate(regacts):
        definitions+=RA.to_p4_code(namespace, reg_name, f'{namespace}regact_{i}')
        definitions+=f"""
        action {namespace}exec_regact_{i}(){{
            {namespace}regact_{i}.execute({namespace}reg_index);
        }}
        """

    list_RA_actions='\n\t\t'.join([f'{namespace}exec_regact_{i};' for i in range(len(regacts))])

    list_RA_entries ='\n\t\t'.join([
            f'({namespace}_SYMBOLID_{sym}): {namespace}exec_regact_{regact_id[sym]}();'
            for i,sym in enumerate(input['sigma'])
        ])

    table_2=f"""
        table tb_run_regact{{
            key = {{
                {namespace}_SYMBOL: exact;
            }}
            actions = {{
                {list_RA_actions}
            }}
            const entries = {{
                {list_RA_entries}
            }}
        }}
    """
    
    print(f"""
    {struct_definitions}
    control {namespace}Control(in ig_metadata_t ig_md, out bit<{bitvecsize}> new_state){{
        {definitions}
        {table_1}
        {table_2}
        {table_3}

        apply {{
            //step 1: custom rule to map packet into transition symbol
            tb_map_packet_to_symbol.apply();
            
            //step 2: run arithmetic operations
            tb_run_regact.apply();

            //step 3: got the numerical representation of the new state, map it back
            new_state={namespace}rv;
            tb_map_rv_to_state.apply();
        }}
    }}
    """)


def allowed_var_names(s): 
    'ensure generated P4 code has valid variable names'
    return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', s)

def check_names(input):
    for name in input['sigma']:
        assert(allowed_var_names(name))
    for name in input['states']:
        assert(allowed_var_names(name))

def main():
    parser = argparse.ArgumentParser(description='Create DFA P4 code snippet from model.')
    parser.add_argument('input', type=str, help='The original DFA json.')
    parser.add_argument('config', type=str,  help='The synthesis output model json.')
    parser.add_argument('--warning', action='store_true')
    args=parser.parse_args()

    input=json.load(open(args.input))
    config=json.load(open(args.config))

    generateP4(input, config, args.warning)

if __name__ == '__main__':
    main()
