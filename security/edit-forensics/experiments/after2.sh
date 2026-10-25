cd "$(dirname "$0")/.."
until grep -q AFTER_DONE results/queue.log; do sleep 30; done
echo "$(date +%H:%M) START exp4" >> results/queue.log
.venv/bin/python experiments/exp4_basefree.py 30 > results/exp4_basefree.log 2>&1
echo "$(date +%H:%M) END exp4 exit=$?" >> results/queue.log
.venv/bin/python src/summarize.py > /dev/null 2>&1
echo ALL_DONE >> results/queue.log
