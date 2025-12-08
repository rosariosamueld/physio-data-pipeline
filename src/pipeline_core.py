import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from .pipeline import summarize_subject  # reuse your existing function


def summarize_all_subjects(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group by subject_id and apply summarize_subject to each group.

    Returns a single DataFrame with one row per subject.
    """
    summaries = []

    for subject_id, sub_df in df.groupby("subject_id"):
        summary_df = summarize_subject(sub_df)
        summaries.append(summary_df)

    if not summaries:
        return pd.DataFrame()

    return pd.concat(summaries, ignore_index=True)


def make_speed_vs_power_figure(summary_df: pd.DataFrame) -> plt.Figure:
    """
    Create a simple scatter + best-fit line plot of
    speed (m/s) vs net metabolic power (W/kg).

    Returns a Matplotlib Figure object.
    """
    x = summary_df["net_metabolic_power_Wkg"]
    y = summary_df["speed_m_per_s"]

    fig, ax = plt.subplots()

    # Scatter points
    ax.scatter(x, y, alpha=0.8)

    # Simple best-fit line using numpy.polyfit
    if len(summary_df) >= 2:
        m, b = np.polyfit(x, y, 1)
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = m * x_line + b
        ax.plot(x_line, y_line, linestyle="--")

        # simple R²
        y_pred = m * x + b
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")

        ax.set_title(f"Speed vs Net Metabolic Power (R² ≈ {r2:.2f})")
    else:
        ax.set_title("Speed vs Net Metabolic Power")


    fig.tight_layout()
    return fig


def make_vo2_time_figure(full_df: pd.DataFrame, subject_id) -> plt.Figure:
    """
    Create a VO2 (mL/min) over time plot for a single subject,
    with rest vs run phases in different lines.
    """
    sub = full_df[full_df["subject_id"] == subject_id].copy()

    if sub.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, f"No data for subject {subject_id}",
                ha="center", va="center")
        ax.axis("off")
        return fig

    sub = sub.sort_values("time_s")

    fig, ax = plt.subplots()

    for phase, phase_df in sub.groupby("phase"):
        ax.plot(phase_df["time_s"], phase_df["VO2_ml_min"], label=str(phase))

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("VO2 (mL/min)")
    ax.set_title(f"VO2 over time – subject {subject_id}")
    ax.legend()
    fig.tight_layout()
    return fig

def make_vo2_time_figure(df, subject_id):
    """
    Create a VO2 vs time figure for a single subject.
    Returns a matplotlib figure object for Streamlit display.
    """
    fig, ax = plt.subplots()
    df = df.sort_values("time_s")

    for phase, sub in df.groupby("phase"):
        ax.plot(sub["time_s"], sub["VO2_ml_min"], label=phase)

    ax.set_title(f"VO2 over time – {subject_id}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("VO2 (mL/min)")
    ax.legend()

    return fig


def summarize_group_text(summary_df: pd.DataFrame) -> str:
    """
    Build a human-readable summary of the filtered group.

    Expects columns:
      - net_metabolic_power_Wkg
      - speed_m_per_s
      - running_economy_ml_kg_min
    """
    n = len(summary_df)
    mean_power = summary_df["net_metabolic_power_Wkg"].mean()
    mean_speed = summary_df["speed_m_per_s"].mean()
    mean_re = summary_df["running_economy_ml_kg_min"].mean()

    # Correlation between power and speed (if at least 2 subjects)
    corr_text = "not enough data to estimate the relationship."
    if n >= 2:
        corr = np.corrcoef(
            summary_df["net_metabolic_power_Wkg"],
            summary_df["speed_m_per_s"],
        )[0, 1]
        if corr > 0.3:
            corr_text = (
                f"a **positive association** between net metabolic power and speed "
                f"(r ≈ {corr:.2f}), suggesting that faster runners tend to have "
                "higher metabolic cost."
            )
        elif corr < -0.3:
            corr_text = (
                f"a **negative association** between net metabolic power and speed "
                f"(r ≈ {corr:.2f})."
            )
        else:
            corr_text = (
                f"a **weak or no clear association** between net metabolic power and speed "
                f"(r ≈ {corr:.2f})."
            )

    # Identify highest / lowest economy subjects
    best_idx = summary_df["running_economy_ml_kg_min"].idxmin()
    worst_idx = summary_df["running_economy_ml_kg_min"].idxmax()

    best_row = summary_df.loc[best_idx]
    worst_row = summary_df.loc[worst_idx]

    summary = f"""
- The current filter includes **{n} subject(s)**.
- Average net metabolic power is approximately **{mean_power:.2f} W/kg**, with an average speed of **{mean_speed:.2f} m/s**.
- Mean running economy is about **{mean_re:.1f} mL·kg⁻¹·min⁻¹**.
- There appears to be {corr_text}
- The most economical runner in this group is **{best_row['subject_id']}** \
with a running economy of **{best_row['running_economy_ml_kg_min']:.1f} mL·kg⁻¹·min⁻¹**.
- The least economical runner is **{worst_row['subject_id']}** \
with **{worst_row['running_economy_ml_kg_min']:.1f} mL·kg⁻¹·min⁻¹**.
"""
    return summary
