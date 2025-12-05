# Physiological Data Pipeline for Metabolic Power and Running Economy

This project demonstrates a reproducible Python pipeline for processing metabolic cart data to calculate **running economy** and **net metabolic power** using physiologically accepted methods.

The workflow reflects procedures commonly used in exercise physiology and biomechanics research, including net oxygen consumption calculations and steady-state window averaging.

The pipeline supports:
- Multi-subject metabolic data ingestion
- Windowed extraction of steady-state rest and running phases
- Committee-standard calculations of:
  - Net VO₂
  - Running economy (mL·kg⁻¹·min⁻¹)
  - Net metabolic power (W·kg⁻¹)
- Subject-level summary export
- VO₂ time-series visualization

This repository is structured as a lightweight, reproducible analysis pipeline suitable for use in research and clinical data workflows.

---

## Project Structure

physio-data-pipeline/
├── data/
│ └── sample_raw_metabolic_data.csv # Example metabolic cart dataset
│
├── src/
│ └── pipeline.py # Main processing pipeline
│
├── outputs/
│ ├── example_summary.csv # Subject-level summary metrics
│ ├── vo2_time_P01.png # VO₂ vs time plots (one per subject)
│ ├── vo2_time_P02.png
│ └── ...
│
├── requirements.txt
└── README.md

---

## Methodology

### Data windows

For each participant:
- **Rest phase** and **run phase** are identified using the `phase` field.
- The final **120 seconds** of each phase are extracted to represent steady-state physiology.

---

### Net gas exchange

Mean values are calculated for each phase:

run_vo2 = mean VO₂ during run window
rest_vo2 = mean VO₂ during rest window
run_vco2 = mean VCO₂ during run window
rest_vco2 = mean VCO₂ during rest window

Net gas exchange:

net VO₂ = run VO₂ − rest VO₂ (mL/min)
net VCO₂ = run VCO₂ − rest VCO₂ (mL/min)

---

### Running economy

Running economy is expressed as:

net VO₂ / body mass


Resulting units:

> **mL·kg⁻¹·min⁻¹**

This aligns with convention used in steady-state metabolic cost research.

---

### Net metabolic power

Energy (kJ/min) = 16.58 × net VO₂ (L/min) + 4.51 × net VCO₂ (L/min)

Conversion to watts and normalization by body mass:

Watts = (kJ/min × 1000) ÷ 60
Power (W/kg) = Watts ÷ body mass


Final output metric:

> **Net metabolic power (W·kg⁻¹)**

---

## Outputs

### Summary table

`outputs/example_summary.csv`

Includes the following columns:

| Variable                         | Units               |
|----------------------------------|---------------------|
| `subject_id`                     | —                   |
| `rest_vo2_ml_min`                | mL/min              |
| `run_vo2_ml_min`                 | mL/min              |
| `rest_vco2_ml_min`               | mL/min              |
| `run_vco2_ml_min`                | mL/min              |
| `net_vo2_ml_min`                 | mL/min              |
| `net_vco2_ml_min`                | mL/min              |
| `running_economy_ml_kg_min`      | mL·kg⁻¹·min⁻¹       |
| `net_metabolic_power_Wkg`        | W·kg⁻¹              |
| `speed_m_per_s`                  | m·s⁻¹               |

---

### Visualization

For each subject, the pipeline produces a VO₂ time-series plot:

outputs/vo2_time_<subject_id>.png


Each plot shows:
- Continuous VO₂ data over time
- Phase separation (rest vs run)
- Visual confirmation of steady-state windows

---

## Running the Pipeline

### 1. Install dependencies

```bash
pip install -r requirements.txt
```
### 2. Run processing

From the repository root:

py src/pipeline.py

This step creates:
- outputs/example_summary.csv
- outputs/vo2_time_*.png

### 3. Outputs

Summary CSV: outputs/example_summary.csv

Plots: outputs/vo2_time_*.png

Each run automatically overwrites existing outputs with updated results.

### 4. Run regression modeling

Open and execute:

notebooks/speed_vs_metabolic_power_regression.ipynb

This generates:

- outputs/speed_vs_metabolic_power_regression.png

- outputs/speed_vs_metabolic_power_summary.csv

## Statistical Modeling

An applied regression analysis explores the relationship between metabolic cost and running speed.

Linear Regression

The following model is fit using ordinary least squares:

speed_m_per_s ~ net_metabolic_power_Wkg

Model Equation

Speed (m/s) = 1.83 + 0.18 × Net Metabolic Power (W/kg)

Interpretation

Results demonstrate a positive association between increasing metabolic power and running speed, consistent with physiological expectations at steady-state submaximal exercise intensities.

The slope coefficient reflects:

β = 0.18 m·s⁻¹ per W·kg⁻¹

95% CI: −0.03 to 0.38

p-value = 0.081

This near-significant trend is consistent with expected small-sample physiology datasets in which between-subject variance limits formal statistical power but effect directions remain physiologically coherent.

Modeling Outputs

Regression plot
outputs/speed_vs_metabolic_power_regression.png

Coefficient table
outputs/speed_vs_metabolic_power_summary.csv

All modeling code is contained within:

notebooks/speed_vs_metabolic_power_regression.ipynb

---

Example Use Cases

This pipeline structure is useful for:

- Steady-state running economy investigations

- Metabolic cost analysis for treadmill or overground trials

- Teaching laboratory workflows for exercise physiology programs

- Demonstrations of reproducible, domain-specific data science pipelines

---

Notes

- Sample data are synthetic and provided for workflow demonstration.

- Methods follow standard gas-exchange calculations used in steady-state running economy and metabolic power research.

- The pipeline can scale to any number of subjects present in the input dataset.

---

Author

Samuel Rosario, PhD
Biomechanics & Exercise Physiology
Clinical data analytics • signal processing • metabolic modeling