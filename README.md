# Physiological Data Pipeline for Metabolic Power and Running Economy

This repository shows an end-to-end Python workflow for analyzing metabolic cart data
from a submaximal running test. It demonstrates how to:

- Ingest raw physiological data (VO2, VCO2, body mass, and speed)
- Isolate resting and steady-state running periods
- Compute metabolic power using the Brockway equation
- Normalize results to body mass (W/kg)
- Calculate **net** metabolic power by subtracting a resting baseline
- Generate subject-level summary tables and example plots

Although the data and values in this repo are synthetic, the code structure reflects
a real workflow used to analyze physiological assessment data in a research/clinical context.

---

## Project Structure

```text
physio-data-pipeline/
├── README.md
├── requirements.txt
├── data/
│   ├── sample_raw_metabolic_data.csv
│   └── sample_subject_metadata.csv      # optional
├── src/
│   ├── __init__.py
│   ├── load_and_preprocess.py
│   ├── metabolic_calculations.py
│   ├── summary_and_outputs.py
│   └── visualization.py
└── outputs/
    ├── example_summary.csv
    └── example_plots.png
