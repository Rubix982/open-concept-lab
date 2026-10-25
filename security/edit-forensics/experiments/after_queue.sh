cd "$(dirname "$0")/.."
until grep -q QUEUE_DONE results/queue.log; do sleep 30; done
echo "$(date +%H:%M) START exp3" >> results/queue.log
.venv/bin/python experiments/exp3_open_vocab.py 30 > results/exp3_open_vocab.log 2>&1
echo "$(date +%H:%M) END exp3 exit=$?" >> results/queue.log
echo AFTER_DONE >> results/queue.log
