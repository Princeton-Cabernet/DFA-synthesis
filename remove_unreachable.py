import json
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create DFA configurations.')
    parser.add_argument('input', type=str)
    args=parser.parse_args()
    input_json=json.load(open(args.input))
    reachable = set()
    successors = {}
    for state in input_json["states"]:
        successors[state] = set()
    for transition in input_json["transitions"]:
        successors[transition[0]].add(transition[2])
    worklist = [input_json["initial"]]
    reachable.add(input_json["initial"])
    while len(worklist) > 0:
        curr = worklist.pop()
        succ = successors[curr]
        for s in succ:
            if not(s in reachable):
                worklist.append(s)
            reachable.add(s)
    print(len(input_json["states"]) - len(reachable))
        

    