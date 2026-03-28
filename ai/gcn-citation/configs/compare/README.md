These are starter comparison configs for `--mode compare-runs`.

They are intentionally a mix of:

- real cached arXiv runs for meaningful comparisons
- quick Cora/debug runs for fast smoke tests
- diverse model/aggregator/sampler choices so you can contrast different research ideas

Typical usage:

```bash
python3 main.py \
  --mode compare-runs \
  --compare-name arxiv-mean-vs-lstm \
  --compare-config-a configs/compare/arxiv_graphsage_numpy_mean.json \
  --compare-config-b configs/compare/arxiv_graphsage_jax_lstm.json
```

Good pairings to try first:

- `arxiv_graphsage_numpy_mean.json` vs `arxiv_graphsage_numpy_pool.json`
- `arxiv_graphsage_numpy_pool.json` vs `arxiv_graphsage_jax_lstm.json`
- `arxiv_graphsage_v2_degree_weighted.json` vs `arxiv_graphsage_v2_with_replacement.json`
- `arxiv_graphsage_jax_lstm.json` vs `arxiv_gat_jax.json`

Larger cached-corpus (`arxiv_max_results=10000`) pairings:

- `arxiv_10k_graphsage_numpy_mean.json` vs `arxiv_10k_graphsage_numpy_pool.json`
- `arxiv_10k_graphsage_numpy_pool.json` vs `arxiv_10k_graphsage_jax_lstm.json`
- `arxiv_10k_graphsage_v2_uniform.json` vs `arxiv_10k_graphsage_v2_degree_weighted.json`
- `arxiv_10k_graphsage_v2_uniform.json` vs `arxiv_10k_graphsage_v2_with_replacement.json`
