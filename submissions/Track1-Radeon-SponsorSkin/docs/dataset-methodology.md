# Dataset Methodology

SponsorSkin keeps its canonical paired-edit dataset independent from any
trainer. Every immediate directory under the dataset root is one auditable
sample:

```text
sample-001/
├── source.png
├── rough_composite.png
├── target.png
├── mask.png
├── logo.png
├── instruction.txt
└── metadata.json
```

`source.png` is the rights-cleared photograph, `rough_composite.png` is the
deterministic exact-logo condition, and `target.png` is the reviewed polished
target. All three and `mask.png` must share dimensions. `logo.png` must retain
transparency.

`metadata.json` records `sample_id`, `split`, `material`, source and logo
creators, licenses, and optional source URL/notes. Split by source photograph,
not by derived crop, to prevent leakage. Use fictional or expressly authorized
logos only.

Validate before adapting data to a trainer:

```bash
python scripts/validate_dataset.py path/to/canonical-dataset \
  --json benchmarks/dataset-validation.json
```

The LoRA pilot starts with 12–20 reviewed pairs at 512 px. It is accepted only
after a Radeon run produces a loadable checkpoint and improves at least 60% of
held-out comparisons without harming outside-mask preservation or logo
fidelity. Otherwise, the release remains the base-model workflow.
