tsp bash -c "python3 genDFA.py examples/zoom_simple.json --two_cond   --num_regact=4 --arith_bin --num_arith=6 --bitvecsize=8 --timeout=1800  --num_split_nodes=1 --jsonpath=/media/data/mengying/P4DFA/eval_seed_1/model_TwoCond_zoom_simple.json.json > /media/data/mengying/P4DFA/eval_seed_1/result_TwoCond_zoom_simple.json.log; python3 simulator.py examples/zoom_simple.json /media/data/mengying/P4DFA/eval_seed_1/model_TwoCond_zoom_simple.json.json >> /media/data/mengying/P4DFA/eval_seed_1/result_TwoCond_zoom_simple.json.log"
