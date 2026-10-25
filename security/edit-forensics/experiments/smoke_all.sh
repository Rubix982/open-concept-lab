cd "$(dirname "$0")/.."
for a in noise finetune spread batch decoy; do
  echo "== $a"; SMOKE=1 .venv/bin/python experiments/exp2_evasion.py $a 1 2>&1 | grep -E "^\{|Traceback|Error|error" -A4 | tail -6
done
echo SMOKE_DONE
