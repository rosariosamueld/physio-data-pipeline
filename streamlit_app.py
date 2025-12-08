import pandas as pd
import streamlit as st

from src.pipeline_core import (
    summarize_all_subjects,
    make_speed_vs_power_figure,
    make_vo2_time_figure,
    make_vo2_compare_figure,
    summarize_group_text,
)

st.title("Metabolic Power & Running Economy – Summary Dashboard")

st.write(
    "Upload a metabolic data CSV (same structure as `sample_raw_metabolic_data.csv`) "
    "to compute subject-level running economy and net metabolic power."
)

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    # Read uploaded data into DataFrame
    df = pd.read_csv(uploaded_file)

    # ---- Column validation ----
    required_cols = [
        "subject_id",
        "phase",
        "time_s",
        "VO2_ml_min",
        "VCO2_ml_min",
        "body_mass_kg",
        "speed_m_per_s",
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(
            "The uploaded file is missing required columns: "
            + ", ".join(missing)
            + ". Please use a file with the same structure as sample_raw_metabolic_data.csv."
        )
        st.stop()
    
    st.subheader("Raw Data (first 10 rows)")
    st.dataframe(df.head(10))

    # Run existing summary logic
    try:
        summary_df = summarize_all_subjects(df)

        # If nothing was computed, stop early
        if summary_df.empty:
            st.warning("No subjects found in the uploaded data.")
            st.stop()

        # --- Sidebar controls ---
        st.sidebar.header("Controls")

        # --- Sidebar help text ---
        st.sidebar.caption(
            "Use the slider to restrict the analysis to runners within a given "
            "net metabolic power range. All tables, plots, and summaries update automatically."
        )

        # Slider limits based on data
        min_power = float(summary_df["net_metabolic_power_Wkg"].min())
        max_power = float(summary_df["net_metabolic_power_Wkg"].max())

        power_range = st.sidebar.slider(
            "Net metabolic power range (W/kg)",
            min_value=round(min_power, 1),
            max_value=round(max_power, 1),
            value=(round(min_power, 1), round(max_power, 1)),
            step=0.1,
        )

        # Filter summary by selected power range
        filtered_summary = summary_df[
            (summary_df["net_metabolic_power_Wkg"] >= power_range[0])
            & (summary_df["net_metabolic_power_Wkg"] <= power_range[1])
        ]

        st.subheader("Subject-level Summary (filtered)")
        if filtered_summary.empty:
            st.warning(
                "No subjects fall within the selected power range. "
                "Try widening the slider in the sidebar."
            )
            st.stop()

        st.dataframe(filtered_summary)

        # Speed vs net metabolic power visualization (filtered)
        st.subheader("Speed vs Net Metabolic Power")
        fig = make_speed_vs_power_figure(filtered_summary)
        st.pyplot(fig)

        # --- Per-subject details based on filtered list ---
        st.subheader("Per-subject Details")

        subject_ids = filtered_summary["subject_id"].unique().tolist()
        selected_subject = st.selectbox("Select a subject", subject_ids)

        # Show that subject's summary row
        st.markdown("**VO₂ over time (rest vs run):**")

        # split layout: plot (wide) + metrics (narrow)
        col_fig, col_info = st.columns([3, 2])

        with col_fig:
            vo2_fig = make_vo2_time_figure(
                df[df["subject_id"] == selected_subject],
                selected_subject,
            )
            st.pyplot(vo2_fig)

        with col_info:
            st.markdown("**Subject summary**")

        # get this subject's summary row from the filtered summary
        subj_row = filtered_summary[
            filtered_summary["subject_id"] == selected_subject
        ].iloc[0]

        re = subj_row["running_economy_ml_kg_min"]
        power = subj_row["net_metabolic_power_Wkg"]
        speed = subj_row["speed_m_per_s"]

        st.metric(
            "Running economy",
            f"{re:.1f} mL·kg⁻¹·min⁻¹",
        )
        st.metric(
            "Net metabolic power",
            f"{power:.2f} W/kg",
        )
        st.metric(
            "Speed",
            f"{speed:.2f} m/s",
        )

        st.caption(
            "Values computed from the final 120 s of rest and run, "
            "using net VO₂/VCO₂ conventions."
        )


        # ----------------------------
        # Multi-subject comparison
        # ----------------------------
        st.subheader("Compare subjects (run-phase VO₂)")

        compare_ids = st.multiselect(
            "Select subjects to compare",
            subject_ids,
            default=subject_ids[:2] if len(subject_ids) >= 2 else subject_ids,
        )

        if compare_ids:
            compare_df = df[df["subject_id"].isin(compare_ids)]

            # Time-aligned comparison figure
            fig_cmp = make_vo2_compare_figure(compare_df, compare_ids)
            st.pyplot(fig_cmp)

            st.caption(
                "Run-phase VO₂ traces are aligned so that time 0 corresponds to the start "
                "of the run for each subject. Shaded regions indicate the final 120 s "
                "used for steady-state calculations."
            )

            # Small metrics table for the compared subjects
            st.markdown("**Compared subjects – key metrics**")

            compare_summary = (
                filtered_summary[
                    filtered_summary["subject_id"].isin(compare_ids)
                ][
                    [
                        "subject_id",
                        "running_economy_ml_kg_min",
                        "net_metabolic_power_Wkg",
                        "speed_m_per_s",
                    ]
                ]
                .sort_values("subject_id")
                .rename(
                    columns={
                        "subject_id": "Subject",
                        "running_economy_ml_kg_min": "Running economy (mL·kg⁻¹·min⁻¹)",
                        "net_metabolic_power_Wkg": "Net power (W/kg)",
                        "speed_m_per_s": "Speed (m/s)",
                    }
                )
            )

            st.dataframe(compare_summary, use_container_width=True)

        else:
            st.info("Select one or more subjects to view a comparison plot.")


        # --- Automated interpretation of the filtered group ---
        st.subheader("Automated Summary of Filtered Group")
        summary_text = summarize_group_text(filtered_summary)
        st.markdown(summary_text)

        # --- Download button in sidebar ---
        st.sidebar.subheader("Download Results")
        csv_bytes = filtered_summary.to_csv(index=False).encode("utf-8")
        st.sidebar.download_button(
        label="Download filtered summary as CSV",
        data=csv_bytes,
        file_name="summary_filtered.csv",
        mime="text/csv",
        )


    except Exception as e:
        st.error(f"Error while summarizing data: {e}")
        st.stop()

else:
    st.info("Please upload a CSV file to begin.")