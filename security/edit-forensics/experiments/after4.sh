cd "$(dirname "$0")/.."
until grep -q FINAL_DONE results/queue.log; do sleep 30; done
echo "$(date +%H:%M) START batch2 (held-out, subspace score)" >> results/queue.log
.venv/bin/python experiments/exp2_evasion.py batch2 > results/exp2_evasion_batch2.log 2>&1
echo "$(date +%H:%M) END batch2 exit=$?" >> results/queue.log
.venv/bin/python src/summarize.py > /dev/null 2>&1
echo REALLY_DONE >> results/queue.log
