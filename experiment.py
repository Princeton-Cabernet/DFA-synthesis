import sys
import json
import itertools
from genDFA import createDFA

if __name__ == '__main__':
    arith_bin = True
    two_cond = True
    four_branch = False
    bitvecsize = 32
    timeout = 1800

    files = ["simple.json"] + ["s%d.json" % i for i in range(2,5)] + ["p%d.json" % i for i in range(2,5)]
    two_slot_list = [True, False]
    num_regact_list = list(range(1,5))

    for two_slot, file, num_regact in itertools.product(two_slot_list, files, num_regact_list):
        path = "examples/%s" % file
        sys.stderr.write("(two_slot, file, num_regact) : (%s, %s, %d)\n" % (two_slot, file, num_regact))
        input_json=json.load(open(path))
        createDFA(input_json, arith_bin, two_cond, two_slot, four_branch, num_regact, bitvecsize, timeout)
