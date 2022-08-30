import json
import sys

if __name__ == '__main__':

    files = ["zoom_simple.json", "mobiledevice.json", "tcp_open.json", "simple.json"] \
            + ["fingerprint_%s.json" % suf for suf in ["16x1", "8x3", "10x3", "12x3", "8x4", "10x4", "12x4"]] \
            + ["s%d.json" % i for i in range(2,5)] + ["p%d.json" % i for i in range(2,5)]

    for file in files:
        path = "examples/%s" % file
        sys.stderr.write("file : %s\n" % ( file))
        input_json=json.load(open(path))
        print("(num_sigma, num_states, num_transition): (%d, %d, %d) " % 
               (len(input_json["sigma"]), len(input_json["states"]), len(input_json["transitions"])))
