import os
import pandas as pd

DATA_PATH = "data/sample_raw_metabolic_data.csv"
OUTPUT_PATH = "outputs/example_summary.csv"


def brockway_metabolic_power(vo2_ml_min: pd.Series,
                             vco2_ml_min: pd.Series) -> pd.Series:
    """
    Compute metabolic power (W) using Brockway (1987).

    VO2 and VCO2 are expected in mL/min.
    """
    vo2_l_min = vo2_ml_min / 1000.0
    vco2_l_min = vco2_ml_min / 1000.0

    # Energy expenditure (kcal/min)
    kcal_min = 3.941 * vo2_l_min + 1.106 * vco2_l_min

    # Convert to Watts (1 kcal/min ≈ 69.78 W)
    watts = kcal_min * 69.78
    return watts


def add_metabolic_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add metabolic power columns (W and W/kg) to the dataframe.

    Assumes df has VO2_ml_min, VCO2_ml_min, and body_mass_kg.
    """
    df = df.copy()
    df["metabolic_power_W"] = brockway_metabolic_power(
        df["VO2_ml_min"],
        df["VCO2_ml_min"]
    )
    df["metabolic_power_W_kg"] = df["metabolic_power_W"] / df["body_mass_kg"]
    return df


def select_last_n_seconds(df: pd.DataFrame,
                          n_seconds: int,
                          time_col: str = "time_s") -> pd.DataFrame:
    """
    Select the last n seconds of data based on a time column.
    """
    df = df.copy()
    max_time = df[time_col].max()
    return df[df[time_col] >= max_time - n_seconds]


def summarize_subject(df: pd.DataFrame,
                      rest_phase: str = "rest",
                      run_phase: str = "run",
                      window_s: int = 120) -> pd.DataFrame:
    """
    Compute summary metrics for a single subject.

    Returns a one-row DataFrame.
    """
    subject_id = df["subject_id"].iloc[0]

    # Add metabolic columns
    df = add_metabolic_columns(df)

    # Rest and run subsets
    rest = df[df["phase"] == rest_phase]
    run = df[df["phase"] == run_phase]

    # Take last `window_s` seconds of each phase
    rest_win = select_last_n_seconds(rest, window_s)
    run_win = select_last_n_seconds(run, window_s)

    rest_mean = rest_win["metabolic_power_W_kg"].mean()
    run_mean = run_win["metabolic_power_W_kg"].mean()
    net_mean = run_mean - rest_mean

    speed = run_win["speed_m_per_s"].mean()

    summary = {
        "subject_id": subject_id,
        "rest_metabolic_power_Wkg": rest_mean,
        "run_metabolic_power_Wkg": run_mean,
        "net_metabolic_power_Wkg": net_mean,
        "speed_m_per_s": speed,
    }

    return pd.DataFrame([summary])


def main():
    # Load full dataset
    df = pd.read_csv(DATA_PATH)

    summaries = []

    # Loop over subjects
    for subject_id, sub_df in df.groupby("subject_id"):
        summary_df = summarize_subject(sub_df)
        summaries.append(summary_df)

    # Combine all subject summaries
    results = pd.concat(summaries, ignore_index=True)

    # Ensure outputs folder exists (helpful if running locally)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Save to CSV
    results.to_csv(OUTPUT_PATH, index=False)

    print("Summary results:")
    print(results)


if __name__ == "__main__":
    main()
