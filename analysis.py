import json
import sys

if __name__ == '__main__':

    files = ["simple.json"] + ["s%d.json" % i for i in range(2,5)] + ["p%d.json" % i for i in range(2,5)]

    for file in files:
        path = "examples/%s" % file
        sys.stderr.write("file : %s\n" % ( file))
        input_json=json.load(open(path))
        print("(num_sigma, num_states, num_transition): (%d, %d, %d) " % 
               (len(input_json["sigma"]), len(input_json["states"]), len(input_json["transitions"])))
