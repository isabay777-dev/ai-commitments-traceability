# F3 release exhibits

Run from the project root:

```sh
Rscript scripts/37_models_F3.R
Rscript scripts/38_governance_F3.R
python3 scripts/39_tables_F3.py
```

Tables 1–4 and captions are English submission materials. CSV files retain exact counts; R exports retain full-precision coefficients and actual estimation samples. Figure 1 and Supplementary Figure S1 have grayscale 600 dpi PNG and vector PDF exports.

The script validates all 190 round pairs, 58 adjudications and six exclusions. It preserves the episode mapping and applies F3 verdicts to the earliest retained anchors. Temporal audit A retains its historical t+1 labels on the F3 population; eight full-at-t+1 versus F3-partial conflicts are exported and disclosed in Table 4. This diagnostic is not harmonised F3 validation. No source data or earlier releases are rewritten.

validation_F3.json records checks, bootstrap settings and versions. source_manifest.json records input SHA-256 values; preserved_source_hashes.json is the pre-edit snapshot.
