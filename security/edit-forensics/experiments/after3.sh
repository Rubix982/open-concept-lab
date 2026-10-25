cd "$(dirname "$0")/.."
until grep -q ALL_DONE results/queue.log; do sleep 30; done
echo "$(date +%H:%M) START noise rerun (self-ablated read-back)" >> results/queue.log
.venv/bin/python experiments/exp2_evasion.py noise 30 > results/exp2_evasion_noise_v2.log 2>&1
echo "$(date +%H:%M) END noise rerun exit=$?" >> results/queue.log
.venv/bin/python src/summarize.py > /dev/null 2>&1
echo FINAL_DONE >> results/queue.log
