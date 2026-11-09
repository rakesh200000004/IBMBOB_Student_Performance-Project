import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib

from src.data_loader import load_data
from src.feature_engineering import engineer_features

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Student Performance Analytics Dashboard",
    page_icon="🎓",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Cached loaders
# ---------------------------------------------------------------------------

@st.cache_data
def get_data():
    df = load_data()
    df = engineer_features(df)
    return df


@st.cache_resource
def get_model():
    return joblib.load("outputs/models/best_model.pkl")


# ---------------------------------------------------------------------------
# Load data and model
# ---------------------------------------------------------------------------
df = get_data()
model = get_model()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🎓 Student Performance Analytics Dashboard")
    st.caption("Data Analytics & Machine Learning")
    st.divider()

    st.markdown("### 📊 Dataset Information")
    st.markdown(f"• **Total records:** {len(df):,}")
    st.markdown(f"• **Features:** {df.shape[1]} columns")
    st.markdown("• **Source:** Kaggle")
    st.divider()

    st.markdown("### 🔍 Filter Data")

    all_genders = sorted(df["gender"].unique().tolist())
    all_races = sorted(df["race_ethnicity"].unique().tolist())
    all_edu = df["parental_level_of_education"].unique().tolist()
    # Preserve natural education order
    edu_order = [
        "some high school",
        "high school",
        "some college",
        "associate's degree",
        "bachelor's degree",
        "master's degree",
    ]
    all_edu_ordered = [e for e in edu_order if e in all_edu] + [
        e for e in all_edu if e not in edu_order
    ]
    all_lunch = sorted(df["lunch"].unique().tolist())
    all_prep = sorted(df["test_preparation_course"].unique().tolist())

    sel_gender = st.multiselect("Gender", options=all_genders, default=all_genders)
    sel_race = st.multiselect(
        "Race/Ethnicity", options=all_races, default=all_races
    )
    sel_edu = st.multiselect(
        "Parental Education",
        options=all_edu_ordered,
        default=all_edu_ordered,
    )
    sel_lunch = st.multiselect("Lunch", options=all_lunch, default=all_lunch)
    sel_prep = st.multiselect(
        "Test Preparation",
        options=all_prep,
        default=all_prep,
    )

    if st.button("🔄 Reset Filters"):
        sel_gender = all_genders
        sel_race = all_races
        sel_edu = all_edu_ordered
        sel_lunch = all_lunch
        sel_prep = all_prep
        st.rerun()

# ---------------------------------------------------------------------------
# Apply filters → filtered dataframe
# ---------------------------------------------------------------------------
fdf = df[
    df["gender"].isin(sel_gender)
    & df["race_ethnicity"].isin(sel_race)
    & df["parental_level_of_education"].isin(sel_edu)
    & df["lunch"].isin(sel_lunch)
    & df["test_preparation_course"].isin(sel_prep)
].copy()

# ---------------------------------------------------------------------------
# Main header
# ---------------------------------------------------------------------------
st.title("Student Performance Analytics Dashboard")
st.markdown(
    "**Data Analytics & Machine Learning** &nbsp;|&nbsp; "
    "IBM SkillsBuild | BharatCares × AICTE &nbsp;|&nbsp; "
    "Rakesh Mondal, B.Tech CSE"
)
st.divider()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "📊 Overview",
        "📈 Performance Analysis",
        "👥 Demographic Analysis",
        "📚 Test Preparation",
        "🔗 Correlation Analysis",
        "🤖 ML Prediction",
        "💡 Key Insights",
    ]
)

# ===========================================================================
# TAB 1 — Overview
# ===========================================================================
with tab1:
    st.subheader("Overview")

    if fdf.empty:
        st.warning("No data matches the current filters.")
    else:
        # KPI row
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Students", f"{len(fdf):,}")
        col2.metric("Avg Math Score", f"{fdf['math_score'].mean():.1f}")
        col3.metric("Avg Reading Score", f"{fdf['reading_score'].mean():.1f}")
        col4.metric("Avg Writing Score", f"{fdf['writing_score'].mean():.1f}")
        col5.metric("Overall Average", f"{fdf['average_score'].mean():.1f}")

        st.markdown("---")

        # Score distribution histogram
        hist_data = pd.melt(
            fdf[["math_score", "reading_score", "writing_score", "average_score"]],
            var_name="Subject",
            value_name="Score",
        )
        subject_labels = {
            "math_score": "Math",
            "reading_score": "Reading",
            "writing_score": "Writing",
            "average_score": "Average",
        }
        hist_data["Subject"] = hist_data["Subject"].map(subject_labels)

        fig_hist = px.histogram(
            hist_data,
            x="Score",
            color="Subject",
            barmode="overlay",
            opacity=0.6,
            nbins=30,
            title="Score Distributions",
            labels={"Score": "Score", "count": "Count"},
        )
        fig_hist.update_layout(bargap=0.05)
        st.plotly_chart(fig_hist, use_container_width=True)

        st.markdown("#### Data Preview (first 20 rows)")
        st.dataframe(fdf.head(20), use_container_width=True)

# ===========================================================================
# TAB 2 — Performance Analysis
# ===========================================================================
with tab2:
    st.subheader("Performance Analysis")

    if fdf.empty:
        st.warning("No data matches the current filters.")
    else:
        # Average score by subject (bar chart)
        subject_means = pd.DataFrame(
            {
                "Subject": ["Math", "Reading", "Writing", "Average"],
                "Mean Score": [
                    fdf["math_score"].mean(),
                    fdf["reading_score"].mean(),
                    fdf["writing_score"].mean(),
                    fdf["average_score"].mean(),
                ],
            }
        )
        fig_bar = px.bar(
            subject_means,
            x="Subject",
            y="Mean Score",
            title="Average Score by Subject",
            text_auto=".1f",
            color="Subject",
        )
        fig_bar.update_traces(textposition="outside")
        st.plotly_chart(fig_bar, use_container_width=True)

        # Boxplots
        box_data = pd.melt(
            fdf[["math_score", "reading_score", "writing_score"]],
            var_name="Subject",
            value_name="Score",
        )
        box_labels = {
            "math_score": "Math",
            "reading_score": "Reading",
            "writing_score": "Writing",
        }
        box_data["Subject"] = box_data["Subject"].map(box_labels)
        fig_box = px.box(
            box_data,
            x="Subject",
            y="Score",
            color="Subject",
            title="Score Distribution by Subject",
        )
        st.plotly_chart(fig_box, use_container_width=True)

        # Scatter plots side by side
        sc_col1, sc_col2 = st.columns(2)
        with sc_col1:
            fig_s1 = px.scatter(
                fdf,
                x="math_score",
                y="reading_score",
                color="gender",
                title="Math Score vs Reading Score",
                labels={
                    "math_score": "Math Score",
                    "reading_score": "Reading Score",
                },
                opacity=0.6,
            )
            st.plotly_chart(fig_s1, use_container_width=True)
        with sc_col2:
            fig_s2 = px.scatter(
                fdf,
                x="math_score",
                y="writing_score",
                color="gender",
                title="Math Score vs Writing Score",
                labels={
                    "math_score": "Math Score",
                    "writing_score": "Writing Score",
                },
                opacity=0.6,
            )
            st.plotly_chart(fig_s2, use_container_width=True)

# ===========================================================================
# TAB 3 — Demographic Analysis
# ===========================================================================
with tab3:
    st.subheader("Demographic Analysis")

    if fdf.empty:
        st.warning("No data matches the current filters.")
    else:
        # --- Gender Analysis ---
        st.markdown("#### Gender Analysis")
        gender_means = (
            fdf.groupby("gender")[["math_score", "reading_score", "writing_score"]]
            .mean()
            .reset_index()
        )
        gender_melted = pd.melt(
            gender_means,
            id_vars="gender",
            var_name="Subject",
            value_name="Mean Score",
        )
        gender_melted["Subject"] = gender_melted["Subject"].map(
            {"math_score": "Math", "reading_score": "Reading", "writing_score": "Writing"}
        )

        g_col1, g_col2 = st.columns(2)
        with g_col1:
            fig_g1 = px.bar(
                gender_melted,
                x="gender",
                y="Mean Score",
                color="Subject",
                barmode="group",
                title="Mean Score by Gender and Subject",
                text_auto=".1f",
            )
            st.plotly_chart(fig_g1, use_container_width=True)
        with g_col2:
            fig_g2 = px.box(
                fdf,
                x="gender",
                y="average_score",
                color="gender",
                title="Average Score Distribution by Gender",
                labels={"average_score": "Average Score", "gender": "Gender"},
            )
            st.plotly_chart(fig_g2, use_container_width=True)

        # --- Race/Ethnicity ---
        st.markdown("#### Race/Ethnicity Analysis")
        race_means = (
            fdf.groupby("race_ethnicity")["average_score"]
            .mean()
            .reset_index()
            .sort_values("average_score")
        )
        fig_race = px.bar(
            race_means,
            x="race_ethnicity",
            y="average_score",
            title="Average Score by Race/Ethnicity Group",
            labels={
                "race_ethnicity": "Race/Ethnicity",
                "average_score": "Mean Average Score",
            },
            text_auto=".1f",
            color="race_ethnicity",
        )
        st.plotly_chart(fig_race, use_container_width=True)

        # --- Parental Education ---
        st.markdown("#### Parental Education Analysis")
        edu_means = (
            fdf.groupby("parental_level_of_education")["average_score"]
            .mean()
            .reset_index()
            .sort_values("average_score")
        )
        fig_edu = px.bar(
            edu_means,
            x="average_score",
            y="parental_level_of_education",
            orientation="h",
            title="Average Score by Parental Education Level",
            labels={
                "parental_level_of_education": "Parental Education",
                "average_score": "Mean Average Score",
            },
            text_auto=".1f",
            color="average_score",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig_edu, use_container_width=True)

# ===========================================================================
# TAB 4 — Test Preparation Analysis
# ===========================================================================
with tab4:
    st.subheader("Test Preparation Analysis")

    if fdf.empty:
        st.warning("No data matches the current filters.")
    else:
        # Test prep vs scores
        prep_means = (
            fdf.groupby("test_preparation_course")[
                ["math_score", "reading_score", "writing_score", "average_score"]
            ]
            .mean()
            .reset_index()
        )
        prep_melted = pd.melt(
            prep_means,
            id_vars="test_preparation_course",
            var_name="Subject",
            value_name="Mean Score",
        )
        prep_melted["Subject"] = prep_melted["Subject"].map(
            {
                "math_score": "Math",
                "reading_score": "Reading",
                "writing_score": "Writing",
                "average_score": "Average",
            }
        )
        fig_prep = px.bar(
            prep_melted,
            x="test_preparation_course",
            y="Mean Score",
            color="Subject",
            barmode="group",
            title="Score Comparison by Test Preparation Status",
            labels={"test_preparation_course": "Test Preparation"},
            text_auto=".1f",
        )
        st.plotly_chart(fig_prep, use_container_width=True)

        # Lunch analysis
        lunch_means = (
            fdf.groupby("lunch")[["math_score", "reading_score", "writing_score"]]
            .mean()
            .reset_index()
        )
        lunch_melted = pd.melt(
            lunch_means,
            id_vars="lunch",
            var_name="Subject",
            value_name="Mean Score",
        )
        lunch_melted["Subject"] = lunch_melted["Subject"].map(
            {"math_score": "Math", "reading_score": "Reading", "writing_score": "Writing"}
        )
        fig_lunch = px.bar(
            lunch_melted,
            x="lunch",
            y="Mean Score",
            color="Subject",
            barmode="group",
            title="Score Comparison by Lunch Type",
            labels={"lunch": "Lunch Type"},
            text_auto=".1f",
        )
        st.plotly_chart(fig_lunch, use_container_width=True)

        # Cross-tab heatmap: test_prep × lunch
        crosstab = (
            fdf.groupby(["test_preparation_course", "lunch"])["average_score"]
            .mean()
            .unstack(fill_value=0)
        )
        fig_heat = px.imshow(
            crosstab,
            text_auto=".1f",
            title="Average Score: Test Prep × Lunch Type",
            labels=dict(
                x="Lunch Type",
                y="Test Preparation",
                color="Mean Avg Score",
            ),
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig_heat, use_container_width=True)

# ===========================================================================
# TAB 5 — Correlation Analysis
# ===========================================================================
with tab5:
    st.subheader("Correlation Analysis")

    if fdf.empty:
        st.warning("No data matches the current filters.")
    else:
        numeric_cols = ["math_score", "reading_score", "writing_score", "average_score", "total_score"]
        corr_matrix = fdf[numeric_cols].corr()

        fig_corr = px.imshow(
            corr_matrix,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="Correlation Heatmap of Numeric Variables",
        )
        st.plotly_chart(fig_corr, use_container_width=True)

        st.markdown("#### Score Pair Scatter Plots")
        p_col1, p_col2, p_col3 = st.columns(3)

        with p_col1:
            fig_p1 = px.scatter(
                fdf,
                x="math_score",
                y="reading_score",
                color="score_group",
                title="Math vs Reading",
                labels={"math_score": "Math Score", "reading_score": "Reading Score"},
                opacity=0.6,
            )
            st.plotly_chart(fig_p1, use_container_width=True)

        with p_col2:
            fig_p2 = px.scatter(
                fdf,
                x="math_score",
                y="writing_score",
                color="score_group",
                title="Math vs Writing",
                labels={"math_score": "Math Score", "writing_score": "Writing Score"},
                opacity=0.6,
            )
            st.plotly_chart(fig_p2, use_container_width=True)

        with p_col3:
            fig_p3 = px.scatter(
                fdf,
                x="reading_score",
                y="writing_score",
                color="score_group",
                title="Reading vs Writing",
                labels={"reading_score": "Reading Score", "writing_score": "Writing Score"},
                opacity=0.6,
            )
            st.plotly_chart(fig_p3, use_container_width=True)

# ===========================================================================
# TAB 6 — Machine Learning Prediction
# ===========================================================================
with tab6:
    st.subheader("Machine Learning Prediction")

    col_input, col_result = st.columns([1, 1])

    with col_input:
        st.subheader("Input Student Profile")
        gender_sel = st.selectbox("Gender", options=["female", "male"])
        race_sel = st.selectbox(
            "Race/Ethnicity",
            options=["group A", "group B", "group C", "group D", "group E"],
        )
        edu_sel = st.selectbox(
            "Parental Education",
            options=[
                "some high school",
                "high school",
                "some college",
                "associate's degree",
                "bachelor's degree",
                "master's degree",
            ],
        )
        lunch_sel = st.selectbox("Lunch Type", options=["standard", "free/reduced"])
        test_prep_sel = st.selectbox(
            "Test Preparation Course", options=["none", "completed"]
        )
        predict_btn = st.button("🔮 Predict Average Score", type="primary")

    with col_result:
        st.subheader("Model Prediction")
        if predict_btn:
            input_df = pd.DataFrame(
                {
                    "gender": [gender_sel],
                    "race_ethnicity": [race_sel],
                    "parental_level_of_education": [edu_sel],
                    "lunch": [lunch_sel],
                    "test_preparation_course": [test_prep_sel],
                }
            )
            prediction = model.predict(input_df)[0]
            st.metric("Predicted Average Score", f"{prediction:.1f} / 100")
            st.info(
                "This is a model prediction based on group-level patterns in the dataset. "
                "It is not a guaranteed individual result."
            )
        else:
            st.markdown(
                "_Fill in the student profile on the left and click_ **🔮 Predict Average Score** _to see the prediction._"
            )

    st.divider()

    # Model Metrics Table
    st.markdown("#### Model Evaluation Metrics")
    metrics_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "metrics.json")
    with open(metrics_path) as f:
        metrics_raw = json.load(f)

    best_model_name = metrics_raw.get("best_model", "")
    model_rows = []
    for model_name in ["Linear Regression", "Decision Tree", "Random Forest"]:
        if model_name in metrics_raw:
            m = metrics_raw[model_name]
            model_rows.append(
                {
                    "Model": model_name,
                    "MAE": round(m["MAE"], 4),
                    "MSE": round(m["MSE"], 4),
                    "RMSE": round(m["RMSE"], 4),
                    "R²": round(m["R2"], 4),
                    "Best": "✅" if model_name == best_model_name else "",
                }
            )
    metrics_df = pd.DataFrame(model_rows)
    st.dataframe(metrics_df, use_container_width=True, hide_index=True)

    # Actual vs Predicted chart (full dataset, unfiltered)
    st.markdown("#### Actual vs Predicted Average Score (Best Model)")
    feature_cols = ["gender", "race_ethnicity", "parental_level_of_education", "lunch", "test_preparation_course"]
    y_actual = df["average_score"].values
    y_pred = model.predict(df[feature_cols])

    avp_df = pd.DataFrame({"Actual": y_actual, "Predicted": y_pred})
    fig_avp = px.scatter(
        avp_df,
        x="Actual",
        y="Predicted",
        title="Actual vs Predicted Average Score (Best Model)",
        labels={"Actual": "Actual Average Score", "Predicted": "Predicted Average Score"},
        opacity=0.5,
    )
    # Diagonal reference line
    score_min = float(min(y_actual.min(), y_pred.min()))
    score_max = float(max(y_actual.max(), y_pred.max()))
    fig_avp.add_shape(
        type="line",
        x0=score_min,
        y0=score_min,
        x1=score_max,
        y1=score_max,
        line=dict(color="red", dash="dash", width=2),
    )
    st.plotly_chart(fig_avp, use_container_width=True)

# ===========================================================================
# TAB 7 — Key Insights
# ===========================================================================
with tab7:
    st.subheader("Key Insights")

    # Compute facts from full (unfiltered) dataset
    avg_math = df["math_score"].mean()
    avg_reading = df["reading_score"].mean()
    avg_writing = df["writing_score"].mean()
    avg_overall = df["average_score"].mean()

    female_avg = df[df["gender"] == "female"]["average_score"].mean()
    male_avg = df[df["gender"] == "male"]["average_score"].mean()
    gender_leader = "Female" if female_avg > male_avg else "Male"

    completed_avg = df[df["test_preparation_course"] == "completed"]["average_score"].mean()
    none_avg = df[df["test_preparation_course"] == "none"]["average_score"].mean()
    test_prep_diff = completed_avg - none_avg

    standard_avg = df[df["lunch"] == "standard"]["average_score"].mean()
    reduced_avg = df[df["lunch"] == "free/reduced"]["average_score"].mean()
    lunch_diff = standard_avg - reduced_avg

    top_edu = (
        df.groupby("parental_level_of_education")["average_score"]
        .mean()
        .idxmax()
    )
    top_edu_avg = df.groupby("parental_level_of_education")["average_score"].mean().max()

    corr_mr = df["math_score"].corr(df["reading_score"])
    corr_mw = df["math_score"].corr(df["writing_score"])
    corr_rw = df["reading_score"].corr(df["writing_score"])

    with open(metrics_path) as f:
        m_data = json.load(f)
    best_r2 = m_data["Linear Regression"]["R2"]
    best_name = m_data["best_model"]

    score_group_counts = df["score_group"].value_counts()
    sg_high = score_group_counts.get("High", 0)
    sg_medium = score_group_counts.get("Medium", 0)
    sg_low = score_group_counts.get("Low", 0)

    top_race = df.groupby("race_ethnicity")["average_score"].mean().idxmax()
    top_race_avg = df.groupby("race_ethnicity")["average_score"].mean().max()

    insights = [
        f"📊 The dataset contains **1,000 students** across 5 demographic race/ethnicity groups.",
        f"📐 The average math score is **{avg_math:.1f}**, reading **{avg_reading:.1f}**, writing **{avg_writing:.1f}**, and overall average **{avg_overall:.1f}**.",
        f"👤 **{gender_leader} students** achieve a higher overall average (Female: {female_avg:.1f}, Male: {male_avg:.1f}).",
        f"📝 Students who **completed test preparation** score on average **{test_prep_diff:.1f} points higher** than those who did not ({completed_avg:.1f} vs {none_avg:.1f}).",
        f"🍽️ Students on **standard lunch** outperform free/reduced lunch students by **{lunch_diff:.1f} points** on average ({standard_avg:.1f} vs {reduced_avg:.1f}).",
        f"🎓 Students whose parents have a **{top_edu}** have the highest average score ({top_edu_avg:.1f}).",
        f"📈 **{top_race}** achieves the highest average score among race/ethnicity groups ({top_race_avg:.1f}).",
        f"🔗 Score correlations are strong: Math–Reading = **{corr_mr:.2f}**, Math–Writing = **{corr_mw:.2f}**, Reading–Writing = **{corr_rw:.2f}**.",
        f"🤖 The best ML model is **{best_name}** with an R² of **{best_r2:.4f}** (using only 5 categorical features, no subject scores).",
        f"🏆 Score group distribution — High: **{sg_high}** students, Medium: **{sg_medium}**, Low: **{sg_low}** (out of 1,000 total).",
        f"⚠️ The low R² ({best_r2:.2f}) reflects that demographic variables alone explain only a modest portion of score variance; individual factors dominate.",
    ]

    for insight in insights:
        st.markdown(f"- {insight}")

    st.divider()
    st.markdown("#### Summary Statistics")
    st.dataframe(
        df[["math_score", "reading_score", "writing_score", "average_score"]]
        .describe()
        .round(2),
        use_container_width=True,
    )
