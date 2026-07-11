# Fine-Tuning and Continued Pre-Training

## Recommended order

1. Build retrieval and evaluation first.
2. Collect high-quality incident and recommendation examples.
3. Perform supervised fine-tuning for format, task behavior, and organization vocabulary.
4. Use preference optimization only with reliable human comparisons.
5. Experiment with continued pre-training only after data governance, deduplication, redaction, and strong baselines.

## Suitable training data

- Sanitized postmortems.
- Evidence-to-hypothesis examples.
- Configuration findings and accepted remediation.
- Runbook selection and execution outcomes.
- Structured incident timelines.
- Expert review comments.
- Vendor and internal technical documentation with license approval.

## Avoid

- Raw secrets.
- Unbounded raw logs without curation.
- Incorrect historical recommendations.
- Unreviewed AI-generated data.
- Personally sensitive data.
- Data without source and license tracking.

## Technique baseline

- PEFT/LoRA for rapid model comparison.
- Full fine-tuning only when justified by measured gains.
- MLflow for experiments and model registry.
- Airflow for dataset, training, and evaluation pipelines.
- MinIO for versioned datasets and artifacts.
