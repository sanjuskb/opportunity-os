# ML Experiment Logs

This directory contains execution logs and metric evaluation summaries for all models trained on the spare laptop.

## Metric Summary Schema
Each run outputs a JSON file to `experiments/runs/<timestamp>_<experiment_name>.json` detailing:
- Commit SHA
- Hyperparameters
- Epoch losses
- Validation NDCG@10, MRR@10, and F1 scores
- Inference latency benchmarks on CPU and GPU
