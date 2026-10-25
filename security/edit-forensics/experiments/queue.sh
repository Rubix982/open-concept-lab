# The overnight run: one job at a time (the machine swaps if two share the GPU).
cd "$(dirname "$0")/.."
run() { echo "$(date +%H:%M) START $*"; .venv/bin/python "$@" > "results/$(basename $1 .py)_${2:-run}.log" 2>&1; echo "$(date +%H:%M) END $* exit=$?"; }
run experiments/exp1_with_base.py gpt2-medium 100
run experiments/exp2_evasion.py noise 30
run experiments/exp2_evasion.py spread 30
run experiments/exp2_evasion.py batch
run experiments/exp2_evasion.py decoy 20
run experiments/exp2_evasion.py finetune 15
run experiments/exp1_with_base.py gpt2-large 50
run experiments/exp1_with_base.py gpt2 100
echo QUEUE_DONE
