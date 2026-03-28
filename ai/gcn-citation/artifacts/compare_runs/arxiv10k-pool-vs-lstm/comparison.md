## Winners

- train_accuracy: arxiv10k-numpy-pool (1.0000)
- val_accuracy: arxiv10k-numpy-pool (0.6220)
- test_accuracy: arxiv10k-jax-lstm (0.6129)

## Comparison Table

| label | model | mode | gat_heads | graphsage_backend | graphsage_variant | graphsage_aggregator | graphsage_sampler | run_name | train_accuracy | val_accuracy | test_accuracy | num_layers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arxiv10k-numpy-pool | graphsage | baseline | 0 | numpy | v1 | pool | uniform | baseline | 1.0000 | 0.6220 | 0.6094 | 2 |
| arxiv10k-jax-lstm | graphsage | baseline | 0 | jax | v1 | lstm | uniform | baseline | 1.0000 | 0.5940 | 0.6129 | 2 |
