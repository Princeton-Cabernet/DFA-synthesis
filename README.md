# Synthesizing DFAs for Tofino switches

This repo contains the source code for our SOSR'22 paper *Synthesizing State Machines for Data Planes*.

### Format

We use a simple JSON dictionary format to describe DFAs:
```
{
    "states" : ["a"],
    "sigma" : ["x"],
    "transitions" : [["a","x","a"]],
    "initial" : "a",
    "accepting" : ["a"]
}
```
Here, `states` is a list of DFA state names and `sigma` is a list of transition symbols. `transitions` specifies a list of transition rules, in the format of (source state, symbol, destination state). 

Note that we require the transition for every (source state, symbol) pair to be well-defined. The synthesizer will reject the input DFA if the list is incomplete.

The DFA definition also includes an initial state and optionally a list of accepting states.

### Synthesizer Usage

To solve for a data-plane mapping of a given DFA, please run `python3 synthesis/genDFA_twb2.py input_DFA.json --jsonpath output_model.json [options]`. Various options are used to add to the complexity of RegisterAction templates; more complex templates lead to better expressiveness but also a slower synthesis.

To use the recommended template complexity level (`TwoBranch`, 3 RegisterActions) used in our paper's Evaluation section, please run:
```
python3 synthesis/genDFA_twb2.py examples/mobiledevice.json \
    --jsonpath output_model_mobiledevice.json \
    --two_cond --two_slot --arith_bin --num_arith=6 --bitvecsize=8 --num_regact=3 --main_fixed \
    --timeout=3600 
```
The solution will be stored in an intermediate representation JSON format. 

The following command will check that the RegisterAction found in the solution indeed accurately corresponds to the state transition rules in the input DFA.
```
python3 output/simulator.py examples/mobiledevice.json output_model_mobiledevice.json
```
### Generating P4 code

We provide a code generator script that outputs a P4 code snippet corresponding to the solution found. Please provide both the original DFA and the solver output to the code generator.

Following the above exapmle, please run:
```
python3 output/p4_code_generator.py examples/mobiledevice.json output_model_mobiledevice.json > output/dfa_impl.p4inc
```

This generates a P4 module that can be included into a larger P4 program. A minimal example of such a program is included as `output/minimal_example.p4`, which can be compiled by `bf-p4c`. Note that you need to manually fill in match-action rules in the generated code to match certain packets into particular transition symbols.

### Citing
If you find this repo useful, please consider citing:

    @article{p4dfa,
        title={Synthesizing State Machines for Data Planes},
        author={Chen, Xiaoqi and Johnson, Andrew and Pan, Mengying and Walker, David},
        booktitle={Proceedings of the Symposium on SDN Research},
        year={2022},
        publisher={ACM}
    }


### License

The project's source code are released here under the [GNU Affero General Public License v3](https://www.gnu.org/licenses/agpl-3.0.html). In particular,
- You are entitled to redistribute the program or its modified version, however you must also make available the full source code and a copy of the license to the recipient. Any modified version or derivative work must also be licensed under the same licensing terms.
- You also must make available a copy of the modified program's source code available, under the same licensing terms, to all users interacting with the modified program remotely through a computer network.
