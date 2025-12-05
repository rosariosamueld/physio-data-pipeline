import os
import pandas as pd
import matplotlib.pyplot as plt

DATA_PATH = "data/sample_raw_metabolic_data.csv"
OUTPUT_PATH = "outputs/example_summary.csv"


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
    Compute subject-level summary metrics using the committee-recommended
    NET VO2/VCO2 conventions.

    Steps:
    - Take the last `window_s` seconds of rest and run.
    - Compute mean VO2 and VCO2 (mL/min) in each window.
    - Compute net VO2 and VCO2 (run - rest).
    - Running economy: net VO2 per kg (mL·kg^-1·min^-1).
    - Net metabolic power (W/kg) from net VO2 and VCO2 using
      16.58 and 4.51 coefficients (kJ/min) converted to W/kg.
    """

    subject_id = df["subject_id"].iloc[0]
    mass_kg = df["body_mass_kg"].iloc[0]

    # Split by phase
    rest = df[df["phase"] == rest_phase].copy()
    run = df[df["phase"] == run_phase].copy()

    # Take last `window_s` seconds in each phase
    rest_win = select_last_n_seconds(rest, window_s)
    run_win = select_last_n_seconds(run, window_s)

    # Mean VO2 and VCO2 (mL/min) in each window
    rest_vo2 = rest_win["VO2_ml_min"].mean()
    run_vo2 = run_win["VO2_ml_min"].mean()

    rest_vco2 = rest_win["VCO2_ml_min"].mean()
    run_vco2 = run_win["VCO2_ml_min"].mean()

    # Net VO2 and VCO2 (run - rest), still in mL/min
    net_vo2 = run_vo2 - rest_vo2
    net_vco2 = run_vco2 - rest_vco2

    # Net VO2 and VCO2 in L/min
    net_vo2_L = net_vo2 / 1000.0
    net_vco2_L = net_vco2 / 1000.0

    # Running economy: net VO2 per kg (mL·kg^-1·min^-1)
    running_economy_ml_kg_min = net_vo2 / mass_kg

    # Energy cost (kJ/min) using committee-recommended coefficients
    energy_kj_min = 16.58 * net_vo2_L + 4.51 * net_vco2_L

    # Convert to W (J/s): kJ/min * 1000 / 60
    power_watts = energy_kj_min * 1000.0 / 60.0

    # Net metabolic power per kg
    power_per_kg = power_watts / mass_kg

    # Average running speed over the run window
    speed_m_per_s = run_win["speed_m_per_s"].mean()

    summary = {
        "subject_id": subject_id,
        "rest_vo2_ml_min": rest_vo2,
        "run_vo2_ml_min": run_vo2,
        "rest_vco2_ml_min": rest_vco2,
        "run_vco2_ml_min": run_vco2,
        "net_vo2_ml_min": net_vo2,
        "net_vco2_ml_min": net_vco2,
        "running_economy_ml_kg_min": running_economy_ml_kg_min,
        "net_metabolic_power_Wkg": power_per_kg,
        "speed_m_per_s": speed_m_per_s,
    }

    return pd.DataFrame([summary])


def plot_vo2_time(df: pd.DataFrame,
                  subject_id: str,
                  out_path: str | None = None) -> None:
    """
    Plot VO2 (mL/min) over time for a single subject,
    with rest vs run phases shown in different lines.

    Saves the figure to out_path if provided.
    """
    fig, ax = plt.subplots()

    # Ensure data is sorted by time
    df = df.sort_values("time_s")

    for phase, sub in df.groupby("phase"):
        ax.plot(sub["time_s"], sub["VO2_ml_min"], label=phase)

    ax.set_title(f"VO2 over time – {subject_id}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("VO2 (mL/min)")
    ax.legend()

    if out_path is not None:
        fig.savefig(out_path, bbox_inches="tight")

    plt.close(fig)


def main():
    # Load full dataset
    df = pd.read_csv(DATA_PATH)

    summaries = []

    # Ensure outputs folder exists (for CSV and plots)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Loop over subjects
    for subject_id, sub_df in df.groupby("subject_id"):
        # Compute summary metrics
        summary_df = summarize_subject(sub_df)
        summaries.append(summary_df)

        # Create VO2 vs time plot for this subject
        plot_path = os.path.join("outputs", f"vo2_time_{subject_id}.png")
        plot_vo2_time(sub_df, subject_id, out_path=plot_path)

    # Combine all subject summaries
    results = pd.concat(summaries, ignore_index=True)

    # Save summary CSV
    results.to_csv(OUTPUT_PATH, index=False)

    print("Summary results:")
    print(results)


if __name__ == "__main__":
    main()
