import os
import pandas as pd
import matplotlib.pyplot as plt

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
