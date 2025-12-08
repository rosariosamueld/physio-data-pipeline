import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm
import streamlit as st

from .pipeline import summarize_subject
from pandas import DataFrame


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


def make_speed_vs_power_figure(df: pd.DataFrame) -> plt.Figure:
    """
    Scatterplot of speed vs net metabolic power with
    OLS regression line and 95% mean CI shading.
    """
    # Drop any rows with missing values in the relevant columns
    df = df.dropna(subset=["net_metabolic_power_Wkg", "speed_m_per_s"])

    x = df["net_metabolic_power_Wkg"].values
    y = df["speed_m_per_s"].values

    # Design matrix with intercept
    X = sm.add_constant(x)

    # OLS fit
    model = sm.OLS(y, X).fit()

    # Grid of x values for smooth line
    x_pred = np.linspace(x.min(), x.max(), 100)
    X_pred = sm.add_constant(x_pred)

    # Predictions + 95% mean CI
    pred = model.get_prediction(X_pred)
    pred_df = pred.summary_frame(alpha=0.05)

    y_pred = pred_df["mean"].values
    ci_lower = pred_df["mean_ci_lower"].values
    ci_upper = pred_df["mean_ci_upper"].values

    # ---- Plotting ----
    fig, ax = plt.subplots(figsize=(7, 5))

    # Scatter
    ax.scatter(x, y, alpha=0.9)

    # Regression line
    ax.plot(x_pred, y_pred, linestyle="--")

    # 95% CI band
    ax.fill_between(x_pred, ci_lower, ci_upper, alpha=0.25)

    # Labels / title
    ax.set_xlabel("Net metabolic power (W/kg)")
    ax.set_ylabel("Speed (m/s)")
    ax.set_title(f"Speed vs Net Metabolic Power (R² ≈ {model.rsquared:.2f})")

    return fig


# Colorblind-safe palette
REST_COLOR = "#4477AA"   # blue
RUN_COLOR  = "#EE6677"   # reddish

def make_vo2_time_figure(
    df: DataFrame,
    subject_id: str,
    window_s: int = 120,
):
    """
    VO₂ (mL/min) over time for a single subject with:
      - colorblind-safe lines
      - steady-state windows shaded
      - simple 95% CI band per phase
    """

    fig, ax = plt.subplots(figsize=(8, 5))

    # sort and split by phase
    df = df.sort_values("time_s")
    rest = df[df["phase"] == "rest"].copy()
    run  = df[df["phase"] == "run"].copy()

    # --- helper to compute mean + 95% CI for a phase ---
    def phase_mean_ci(phase_df):
        y = phase_df["VO2_ml_min"].to_numpy(dtype=float)
        mean = float(y.mean())
        if len(y) > 1:
            sem = y.std(ddof=1) / np.sqrt(len(y))
            half_ci = 1.96 * sem
        else:
            half_ci = 0.0
        return mean, mean - half_ci, mean + half_ci

    # REST line + CI band
    if not rest.empty:
        rest_mean, rest_low, rest_high = phase_mean_ci(rest)
        t_rest = rest["time_s"].to_numpy(dtype=float)

        ax.plot(
            t_rest,
            rest["VO2_ml_min"],
            color=REST_COLOR,
            linestyle="--",
            marker="o",
            label=f"rest (mean {rest_mean:.0f} mL/min)",
        )

        ax.fill_between(
            t_rest,
            np.full_like(t_rest, rest_low, dtype=float),
            np.full_like(t_rest, rest_high, dtype=float),
            color=REST_COLOR,
            alpha=0.15,
            linewidth=0,
        )

        # steady-state window shading (last `window_s` s of rest)
        rest_ss_end = rest["time_s"].max()
        rest_ss_start = max(rest_ss_end - window_s, rest["time_s"].min())
        ax.axvspan(
            rest_ss_start,
            rest_ss_end,
            color=REST_COLOR,
            alpha=0.08,
        )

    # RUN line + CI band
    if not run.empty:
        run_mean, run_low, run_high = phase_mean_ci(run)
        t_run = run["time_s"].to_numpy(dtype=float)

        ax.plot(
            t_run,
            run["VO2_ml_min"],
            color=RUN_COLOR,
            linestyle="-",
            marker="o",
            label=f"run (mean {run_mean:.0f} mL/min)",
        )

        ax.fill_between(
            t_run,
            np.full_like(t_run, run_low, dtype=float),
            np.full_like(t_run, run_high, dtype=float),
            color=RUN_COLOR,
            alpha=0.15,
            linewidth=0,
        )

        # steady-state window shading (last `window_s` s of run)
        run_ss_end = run["time_s"].max()
        run_ss_start = max(run_ss_end - window_s, run["time_s"].min())
        ax.axvspan(
            run_ss_start,
            run_ss_end,
            color=RUN_COLOR,
            alpha=0.08,
        )

    # axes formatting
    ax.set_title(f"VO₂ over time – {subject_id}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("VO₂ (mL/min)")

    ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.6)

    # Legend bottom-right so it stays off the shaded windows
    ax.legend(
        title="Phase",
        loc="lower right",
        frameon=True,
        framealpha=0.9,
        facecolor="white",
    )

    fig.tight_layout()
    return fig


def make_vo2_compare_figure(
    df: DataFrame,
    subject_ids: list[str],
    window_s: int = 120,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8, 5))

    df = (
        df.sort_values("time_s")
          .copy()
    )

    df = df[
        (df["subject_id"].isin(subject_ids)) &
        (df["phase"] == "run")
    ]

    if df.empty:
        ax.text(
            0.5, 0.5,
            "No run-phase data for selected subjects.",
            ha="center", va="center", transform=ax.transAxes
        )
        ax.set_axis_off()
        fig.tight_layout()
        return fig

    for sid in subject_ids:
        sub = df[df["subject_id"] == sid]
        if sub.empty:
            continue

        sub = sub.sort_values("time_s")
        t = sub["time_s"].to_numpy(dtype=float)
        vo2 = sub["VO2_ml_min"].to_numpy(dtype=float)

        # Align run start to t=0
        t_rel = t - t[0]

        ax.plot(
            t_rel,
            vo2,
            label=str(sid),
            linewidth=2.0,
            alpha=0.9,
        )

        # Shade steady-state window
        end_t = t_rel.max()
        start_t = max(end_t - window_s, t_rel.min())
        ax.axvspan(
            start_t,
            end_t,
            alpha=0.08,
        )

    ax.set_title("Run-phase VO₂ comparison (aligned to start of run)")
    ax.set_xlabel("Time since run start (s)")
    ax.set_ylabel("VO₂ (mL/min)")
    ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.6)
    ax.legend(title="Subject", loc="upper right", frameon=True, framealpha=0.9)

    fig.tight_layout()
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
