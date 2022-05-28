# Video Fingerprinting as DFAs

Please run `generate.py` to convert video chunk sizes into DFAs. Note that by default the script only generates 10 DFAs using the first 10 fingerprints -- you shouldn't need more, but can use `-N 1000` to get more.

Other parameters:
 - `--num_symbols` controls how we quantize the chunk sizes into symbols A-Z (which is 26 symbols). You can quantize into up to 52 symbols.
 - `--MTU` specifies a "packet size" (which should be 1450-1500 in real networks), and we translate each chunk into a sequence of "0"s (downstream packets) and an "1" (upstream request). 

After generating the json files, you should run `python3 ../../compose_simultaneous.py size_[0-3].json` to compose 4 fingerprint DFAs into one big DFA. The big DFA takes in the same symbol and advance each underlying DFA individually.
