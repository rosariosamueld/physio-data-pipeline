# Physiological Data Pipeline for Metabolic Power and Running Economy

## Live Interactive Dashboard

**Try the app here:**
https://physio-data-pipeline-iswwfduefm4d3sn5uvxbkm.streamlit.app/

This project demonstrates a reproducible Python pipeline for processing metabolic cart data to calculate **running economy** and **net metabolic power** using physiologically accepted methods.

The workflow reflects procedures commonly used in exercise physiology and biomechanics research, including net oxygen consumption calculations, steady-state window averaging, and exploratory statistical modeling.

The pipeline supports:

- Multi-subject metabolic data ingestion
- Windowed extraction of steady-state rest and running phases
- Committee-standard calculations of:
  - Net VO₂
  - Running economy (mL·kg⁻¹·min⁻¹)
  - Net metabolic power (W·kg⁻¹)
- Subject-level summary metric export
- Regression modeling of speed–metabolic cost relationships
- Interactive visualization via Streamlit:
  - VO₂ time-series with confidence bands
  - Per-subject metric panels
  - Cross-subject run-phase comparisons
  - Power-based filtering and CSV export

This repository is structured as a lightweight, reproducible analysis pipeline suitable for use in research and clinical data workflows.

---

## Project Structure

```text
physio-data-pipeline/
├── data/
│   └── sample_raw_metabolic_data.csv      # Example metabolic cart dataset
│
├── notebooks/
│   └── speed_vs_metabolic_power_regression.ipynb
│                                         # Regression modeling analysis
│
├── outputs/
│   ├── example_summary.csv                # Subject-level summary metrics
│   ├── speed_vs_metabolic_power_regression.png
│   ├── speed_vs_metabolic_power_summary.csv
│   ├── vo2_time_P01.png                   # VO₂ vs time plots (one per subject)
│   └── ...
│
├── src/
│   ├── pipeline.py                        # End-to-end processing runner
│   └── pipeline_core.py                  # Core calculation + plotting utilities
│
├── streamlit_app.py                      # Interactive visualization dashboard
├── requirements.txt
└── README.md
```
---

## Methodology

### Data windows

For each participant:
- **Rest phase** and **run phase** are identified using the `phase` field.
- The final **120 seconds** of each phase are extracted to represent steady-state physiology.

---

### Net gas exchange

Mean values are calculated for each phase:

> run_vo2 = mean VO₂ during run window

> rest_vo2 = mean VO₂ during rest window

> run_vco2 = mean VCO₂ during run window

> rest_vco2 = mean VCO₂ during rest window

Net gas exchange:

> **net VO₂ = run VO₂ − rest VO₂ (mL/min)**

> **net VCO₂ = run VCO₂ − rest VCO₂ (mL/min)**

---

### Running economy

Running economy is expressed as:

> net VO₂ / body mass


Resulting units:

> **mL·kg⁻¹·min⁻¹**

This aligns with convention used in steady-state metabolic cost research.

---

### Net metabolic power

> Energy (kJ/min) = 16.58 × net VO₂ (L/min) + 4.51 × net VCO₂ (L/min)

Conversion to watts and normalization by body mass:

> Watts = (kJ/min × 1000) ÷ 60
> Power (W/kg) = Watts ÷ body mass


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

The project produces both static and interactive visualizations for metabolic inspection and comparison.

**Static outputs (batch pipeline):**

For each subject, the pipeline generates VO₂ time-series plots:

`outputs/vo2_time_<subject_id>.png`

Each plot includes:

- Continuous VO₂ data over time
- Phase separation (rest vs run)
- Highlighted steady-state windows
- Phase-averaged confidence interval shading

Additionally, regression modeling outputs include:

`outputs/speed_vs_metabolic_power_regression.png`

showing the relationship between net metabolic power and running speed with confidence bands.

**Interactive outputs (Streamlit dashboard):**

The dashboard enables dynamic visualization, including:

- VO₂ time-series for selected subjects with CI bands
- Side-by-side subject metric panels
- Multi-subject run-phase VO₂ comparisons aligned to run onset
- Power-based filtering of displayed subjects

---

## Running the Pipeline

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

## Streamlit Dashboard

An interactive Streamlit dashboard is included for dynamic exploration of metabolic and performance metrics.

The dashboard supports:

- Uploading metabolic CSV files
- Automatic computation of:
  - Running economy
  - Net metabolic power
  - Subject-level summaries
- Group-level visualization:
  - Speed vs net metabolic power scatter and regression trend
- Subject-level visualization:
  - VO₂ time-series by experimental phase
- Interactive filtering using net metabolic power ranges
- On-demand download of filtered summary tables

### Run the dashboard locally

From the repository root:

```bash
py -m streamlit run streamlit_app.py
```

## Statistical Modeling

An applied regression analysis explores the relationship between metabolic cost and running speed.

**Linear Regression**

The following model is fit using ordinary least squares:

> speed_m_per_s ~ net_metabolic_power_Wkg

Model Equation

> speed = β0​ + β1​ × net metabolic power

> Speed (m/s) = 1.83 + 0.18 × Net Metabolic Power (W/kg)

The slope coefficient reflects:

> β = 0.18 m·s⁻¹ per W·kg⁻¹

> 95% CI: −0.03 to 0.38

> p-value = 0.081

**Interpretation**

Running speed was modeled as a function of net metabolic power (W·kg⁻¹) using ordinary least squares (statsmodels OLS).

**Regression results:**

| Parameter              | Estimate                         | 95% CI          | p-value |
|------------------------|----------------------------------|------------------|---------|
| Intercept              | 1.83 m/s                         | [0.22, 3.45]    | 0.029   |
| Net metabolic power    | 0.18 m·s⁻¹ per W·kg⁻¹            | [-0.03, 0.38]   | 0.081   |

**Model interpretation**

- Higher net metabolic power tended to be associated with faster running speeds.
- Each additional 1 W·kg⁻¹ of metabolic power corresponded to an approximate increase of **0.18 m·s⁻¹** in speed.
- Although the slope estimate was positive, the relationship did not reach conventional statistical significance (*p* = 0.081), likely reflecting the limited sample size (*n* = 15).

**Modeling outputs**

Regression plot  
`outputs/speed_vs_metabolic_power_regression.png`

Coefficient table  
`outputs/speed_vs_metabolic_power_summary.csv`

All modeling code is contained within:

`notebooks/speed_vs_metabolic_power_regression.ipynb`

---

## Interactive Dashboard (Streamlit)

An interactive dashboard has been implemented using **Streamlit** to provide real-time visualization and exploration of subject-level metabolic data.

### Features

The dashboard allows users to:

- Upload metabolic cart CSV files directly
- Compute subject-level summary metrics (running economy, net metabolic power, speed)
- Filter subjects by net metabolic power range
- View **VO₂ time-series plots** for individual subjects with:
  - Colorblind-safe line styling
  - 95% confidence interval bands per phase
  - Highlighted steady-state windows
- Display **side-by-side subject metrics**
- **Compare multiple subjects simultaneously**:
  - Run-phase VO₂ traces aligned to run onset (time = 0)
  - Overlaid plots with steady-state window shading
  - Summary comparison table for economy, power, and speed
- Download filtered summary metrics as CSV

### Launching the dashboard locally

From the repository root:

```bash
py -m streamlit run streamlit_app.py

```
### Reproducibility

**Brief setup instructions:**

Run the full pipeline:
```bash
pip install -r requirements.txt
py src/pipeline.py
```
**Re-run regression notebook:**

`jupyter notebook notebooks/speed_vs_metabolic_power_regression.ipynb`

---
**Example Use Cases**

This pipeline structure is useful for:

- Steady-state running economy investigations

- Metabolic cost analysis for treadmill or overground trials

- Teaching laboratory workflows for exercise physiology programs

- Demonstrations of reproducible, domain-specific data science pipelines

---

**Notes**

- Sample data are synthetic and provided for workflow demonstration.

- Methods follow standard gas-exchange calculations used in steady-state running economy and metabolic power research.

- The pipeline can scale to any number of subjects present in the input dataset.

---

**Author**

**Samuel Rosario**, PhD
Biomechanics & Exercise Physiology
Clinical data analytics • signal processing • metabolic modeling
