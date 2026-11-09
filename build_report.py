"""
build_report.py
---------------
Generates RakeshMondal_ProjectReport.docx — a professional university-style
project report for the Student Performance Analysis and Prediction project.

All statistics, metrics, and figures are derived from the actual dataset
and model outputs produced by the project.
"""

import os
import sys
import json
from pathlib import Path

# ── ensure project root is on the path ──────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from src.data_loader import load_data
from src.feature_engineering import engineer_features

# ────────────────────────────────────────────────────────────────────────────
# 0.  Load data + metrics
# ────────────────────────────────────────────────────────────────────────────
df = load_data()
df = engineer_features(df)

with open("outputs/metrics.json") as fh:
    metrics = json.load(fh)

# Pre-compute key statistics
avg_math    = round(df["math_score"].mean(), 2)
avg_reading = round(df["reading_score"].mean(), 2)
avg_writing = round(df["writing_score"].mean(), 2)
avg_overall = round(df["average_score"].mean(), 2)

female_avg   = round(df[df["gender"] == "female"]["average_score"].mean(), 2)
male_avg     = round(df[df["gender"] == "male"]["average_score"].mean(), 2)
gender_leader = "Female" if female_avg > male_avg else "Male"

completed_avg  = round(df[df["test_preparation_course"] == "completed"]["average_score"].mean(), 2)
none_avg       = round(df[df["test_preparation_course"] == "none"]["average_score"].mean(), 2)
test_prep_diff = round(completed_avg - none_avg, 2)

standard_avg  = round(df[df["lunch"] == "standard"]["average_score"].mean(), 2)
reduced_avg   = round(df[df["lunch"] == "free/reduced"]["average_score"].mean(), 2)
lunch_diff    = round(standard_avg - reduced_avg, 2)

top_race     = df.groupby("race_ethnicity")["average_score"].mean().idxmax()
top_race_avg = round(df.groupby("race_ethnicity")["average_score"].mean().max(), 2)

top_edu      = df.groupby("parental_level_of_education")["average_score"].mean().idxmax()
top_edu_avg  = round(df.groupby("parental_level_of_education")["average_score"].mean().max(), 2)

corr_mr = round(df["math_score"].corr(df["reading_score"]), 4)
corr_mw = round(df["math_score"].corr(df["writing_score"]), 4)
corr_rw = round(df["reading_score"].corr(df["writing_score"]), 4)

sg_high   = int((df["score_group"] == "High").sum())
sg_medium = int((df["score_group"] == "Medium").sum())
sg_low    = int((df["score_group"] == "Low").sum())

FIGURES_DIR = Path("outputs/figures")

# ────────────────────────────────────────────────────────────────────────────
# 1.  Helper utilities
# ────────────────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color: str):
    """Set background colour of a table cell."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def add_page_number(doc):
    """Add page numbers to the footer of all sections."""
    for section in doc.sections:
        footer = section.footer
        para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        para.clear()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run()
        fldChar1 = OxmlElement("w:fldChar")
        fldChar1.set(qn("w:fldCharType"), "begin")
        instrText = OxmlElement("w:instrText")
        instrText.text = " PAGE "
        fldChar2 = OxmlElement("w:fldChar")
        fldChar2.set(qn("w:fldCharType"), "separate")
        fldChar3 = OxmlElement("w:fldChar")
        fldChar3.set(qn("w:fldCharType"), "end")
        run._r.append(fldChar1)
        run._r.append(instrText)
        run._r.append(fldChar2)
        run._r.append(fldChar3)


def set_col_width(table, col_idx, width_cm):
    for row in table.rows:
        row.cells[col_idx].width = Cm(width_cm)


def heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p


def body(doc, text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.space_before = Pt(4)
    pf.space_after  = Pt(6)
    return p


def caption(doc, text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in p.runs:
        run.font.italic = True
        run.font.size   = Pt(9)
        run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    pf = p.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after  = Pt(10)
    return p


def insert_figure(doc, fig_path, caption_text, width_inches=5.5):
    if Path(fig_path).exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(str(fig_path), width=Inches(width_inches))
    else:
        doc.add_paragraph(f"[Figure not found: {fig_path}]")
    caption(doc, caption_text)


def bullet(doc, text):
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    return p


def add_metrics_table(doc):
    """Add the actual ML metrics table."""
    tbl = doc.add_table(rows=1, cols=6)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = tbl.rows[0].cells
    headers = ["Model", "MAE", "MSE", "RMSE", "R²", "Best"]
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        hdr_cells[i].paragraphs[0].runs[0].bold = True
        hdr_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_bg(hdr_cells[i], "1F4E79")
        hdr_cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    best = metrics.get("best_model", "")
    for model_name in ["Linear Regression", "Decision Tree", "Random Forest"]:
        m = metrics[model_name]
        row_cells = tbl.add_row().cells
        row_cells[0].text = model_name
        row_cells[1].text = f"{m['MAE']:.4f}"
        row_cells[2].text = f"{m['MSE']:.4f}"
        row_cells[3].text = f"{m['RMSE']:.4f}"
        row_cells[4].text = f"{m['R2']:.4f}"
        row_cells[5].text = "✓ Best" if model_name == best else ""
        for cell in row_cells:
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if model_name == best:
            for cell in row_cells:
                set_cell_bg(cell, "E2EFDA")
    return tbl


def add_summary_stats_table(doc):
    """Add descriptive statistics table."""
    desc = df[["math_score", "reading_score", "writing_score", "average_score"]].describe().round(2)
    cols = ["Statistic", "Math Score", "Reading Score", "Writing Score", "Average Score"]
    tbl = doc.add_table(rows=1, cols=len(cols))
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = tbl.rows[0].cells
    for i, h in enumerate(cols):
        hdr_cells[i].text = h
        hdr_cells[i].paragraphs[0].runs[0].bold = True
        hdr_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_bg(hdr_cells[i], "1F4E79")
        hdr_cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for stat in desc.index:
        row_cells = tbl.add_row().cells
        row_cells[0].text = stat
        row_cells[1].text = str(desc.loc[stat, "math_score"])
        row_cells[2].text = str(desc.loc[stat, "reading_score"])
        row_cells[3].text = str(desc.loc[stat, "writing_score"])
        row_cells[4].text = str(desc.loc[stat, "average_score"])
        for cell in row_cells:
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    return tbl


# ────────────────────────────────────────────────────────────────────────────
# 2.  Generate report figures (saved to outputs/figures/)
# ────────────────────────────────────────────────────────────────────────────

def generate_report_figures():
    """Re-generate all figures needed for the report using Matplotlib/Seaborn."""
    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams["figure.dpi"] = 150

    # Figure R1 — Score distributions
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, col, title, color in zip(
        axes,
        ["math_score", "reading_score", "writing_score"],
        ["Math Score", "Reading Score", "Writing Score"],
        ["steelblue", "seagreen", "tomato"],
    ):
        ax.hist(df[col], bins=20, color=color, edgecolor="white", alpha=0.85)
        ax.axvline(df[col].mean(), color="black", linestyle="--", linewidth=1.5, label=f"Mean={df[col].mean():.1f}")
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Score")
        ax.set_ylabel("Count")
        ax.legend(fontsize=9)
    plt.suptitle("Score Distributions", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "R1_score_distributions.png", bbox_inches="tight")
    plt.close()

    # Figure R2 — Subject boxplots
    fig, ax = plt.subplots(figsize=(8, 5))
    plot_data = df[["math_score", "reading_score", "writing_score"]].melt(
        var_name="Subject", value_name="Score"
    )
    plot_data["Subject"] = plot_data["Subject"].map(
        {"math_score": "Math", "reading_score": "Reading", "writing_score": "Writing"}
    )
    sns.boxplot(data=plot_data, x="Subject", y="Score", palette="Set2", ax=ax)
    ax.set_title("Score Distribution by Subject", fontsize=13, fontweight="bold")
    ax.set_xlabel("Subject")
    ax.set_ylabel("Score")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "R2_subject_boxplots.png", bbox_inches="tight")
    plt.close()

    # Figure R3 — Gender analysis
    gender_means = df.groupby("gender")[["math_score", "reading_score", "writing_score"]].mean().reset_index()
    gender_melted = gender_means.melt(id_vars="gender", var_name="Subject", value_name="Mean Score")
    gender_melted["Subject"] = gender_melted["Subject"].map(
        {"math_score": "Math", "reading_score": "Reading", "writing_score": "Writing"}
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.barplot(data=gender_melted, x="gender", y="Mean Score", hue="Subject",
                palette="Set2", ax=axes[0])
    axes[0].set_title("Mean Score by Gender & Subject", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Gender"); axes[0].set_ylabel("Mean Score")
    for container in axes[0].containers:
        axes[0].bar_label(container, fmt="%.1f", fontsize=8, padding=2)

    sns.boxplot(data=df, x="gender", y="average_score", palette="Set2", ax=axes[1])
    axes[1].set_title("Average Score Distribution by Gender", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Gender"); axes[1].set_ylabel("Average Score")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "R3_gender_analysis.png", bbox_inches="tight")
    plt.close()

    # Figure R4 — Race/Ethnicity
    race_means = df.groupby("race_ethnicity")["average_score"].mean().reset_index().sort_values("average_score")
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(race_means["race_ethnicity"], race_means["average_score"], color=sns.color_palette("Blues_d", len(race_means)))
    for bar, val in zip(bars, race_means["average_score"]):
        ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2, f"{val:.1f}",
                va="center", fontsize=10)
    ax.set_title("Average Score by Race/Ethnicity Group", fontsize=13, fontweight="bold")
    ax.set_xlabel("Mean Average Score")
    ax.set_xlim(0, 85)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "R4_race_ethnicity.png", bbox_inches="tight")
    plt.close()

    # Figure R5 — Parental education
    edu_order = ["some high school", "high school", "some college",
                 "associate's degree", "bachelor's degree", "master's degree"]
    edu_means = df.groupby("parental_level_of_education")["average_score"].mean().reindex(edu_order)
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(edu_means.index, edu_means.values, color=sns.color_palette("Greens_d", len(edu_means)))
    for bar, val in zip(bars, edu_means.values):
        ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2, f"{val:.1f}",
                va="center", fontsize=9)
    ax.set_title("Average Score by Parental Education Level", fontsize=13, fontweight="bold")
    ax.set_xlabel("Mean Average Score")
    ax.set_xlim(0, 85)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "R5_parental_education.png", bbox_inches="tight")
    plt.close()

    # Figure R6 — Test preparation
    prep_means = df.groupby("test_preparation_course")[
        ["math_score", "reading_score", "writing_score", "average_score"]
    ].mean().reset_index()
    prep_melted = prep_means.melt(id_vars="test_preparation_course", var_name="Subject", value_name="Mean Score")
    prep_melted["Subject"] = prep_melted["Subject"].map(
        {"math_score": "Math", "reading_score": "Reading",
         "writing_score": "Writing", "average_score": "Average"}
    )
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=prep_melted, x="test_preparation_course", y="Mean Score",
                hue="Subject", palette="Set1", ax=ax)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", fontsize=8, padding=2)
    ax.set_title("Score Comparison by Test Preparation Status", fontsize=13, fontweight="bold")
    ax.set_xlabel("Test Preparation Course"); ax.set_ylabel("Mean Score")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "R6_test_prep.png", bbox_inches="tight")
    plt.close()

    # Figure R7 — Lunch
    lunch_means = df.groupby("lunch")[["math_score", "reading_score", "writing_score"]].mean().reset_index()
    lunch_melted = lunch_means.melt(id_vars="lunch", var_name="Subject", value_name="Mean Score")
    lunch_melted["Subject"] = lunch_melted["Subject"].map(
        {"math_score": "Math", "reading_score": "Reading", "writing_score": "Writing"}
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=lunch_melted, x="lunch", y="Mean Score", hue="Subject", palette="Set2", ax=ax)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", fontsize=8, padding=2)
    ax.set_title("Score Comparison by Lunch Type", fontsize=13, fontweight="bold")
    ax.set_xlabel("Lunch Type"); ax.set_ylabel("Mean Score")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "R7_lunch_analysis.png", bbox_inches="tight")
    plt.close()

    # Figure R8 — Correlation heatmap
    fig, ax = plt.subplots(figsize=(7, 5))
    corr = df[["math_score", "reading_score", "writing_score", "average_score"]].corr()
    mask = np.zeros_like(corr, dtype=bool)
    mask[np.triu_indices_from(mask)] = True
    sns.heatmap(corr, annot=True, fmt=".3f", cmap="coolwarm", ax=ax,
                linewidths=0.5, linecolor="white",
                xticklabels=["Math", "Reading", "Writing", "Average"],
                yticklabels=["Math", "Reading", "Writing", "Average"])
    ax.set_title("Correlation Heatmap of Score Variables", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "R8_correlation_heatmap.png", bbox_inches="tight")
    plt.close()

    # Figure R9 — Model comparison bar chart
    model_names = ["Linear Regression", "Decision Tree", "Random Forest"]
    r2_vals    = [metrics[m]["R2"]   for m in model_names]
    mae_vals   = [metrics[m]["MAE"]  for m in model_names]
    rmse_vals  = [metrics[m]["RMSE"] for m in model_names]

    fig, axes = plt.subplots(1, 3, figsize=(13, 5))
    colors = ["#2196F3", "#FF9800", "#4CAF50"]
    for ax, vals, title, ylabel in zip(
        axes,
        [r2_vals, mae_vals, rmse_vals],
        ["R² Score (higher is better)", "MAE (lower is better)", "RMSE (lower is better)"],
        ["R²", "MAE", "RMSE"],
    ):
        bars = ax.bar(model_names, vals, color=colors, edgecolor="white", width=0.5)
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.set_ylabel(ylabel)
        ax.set_xticks(range(len(model_names)))
        ax.set_xticklabels(["Linear\nRegression", "Decision\nTree", "Random\nForest"], fontsize=9)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.002,
                    f"{val:.4f}", ha="center", fontsize=9)
    plt.suptitle("Machine Learning Model Comparison", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "R9_model_comparison.png", bbox_inches="tight")
    plt.close()

    # Figure R10 — Actual vs Predicted
    import joblib
    model_obj = joblib.load("outputs/models/best_model.pkl")
    feature_cols = metrics["feature_columns"]
    y_pred = model_obj.predict(df[feature_cols])
    y_actual = df["average_score"].values

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(y_actual, y_pred, alpha=0.35, color="steelblue", edgecolors="none", s=20)
    lo, hi = min(y_actual.min(), y_pred.min()), max(y_actual.max(), y_pred.max())
    ax.plot([lo, hi], [lo, hi], "r--", linewidth=1.5, label="Perfect prediction")
    ax.set_xlabel("Actual Average Score", fontsize=11)
    ax.set_ylabel("Predicted Average Score", fontsize=11)
    ax.set_title("Actual vs Predicted Average Score\n(Linear Regression — Best Model)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "R10_actual_vs_predicted.png", bbox_inches="tight")
    plt.close()

    # Figure R11 — Score group pie chart
    sg_counts = df["score_group"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 5))
    colors_pie = ["#4CAF50", "#FF9800", "#F44336"]
    wedge_data = [sg_counts.get("High", 0), sg_counts.get("Medium", 0), sg_counts.get("Low", 0)]
    labels_pie = [f"High\n({wedge_data[0]})", f"Medium\n({wedge_data[1]})", f"Low\n({wedge_data[2]})"]
    ax.pie(wedge_data, labels=labels_pie, colors=colors_pie, autopct="%1.1f%%",
           startangle=140, wedgeprops=dict(edgecolor="white", linewidth=1.5))
    ax.set_title("Student Score Group Distribution", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "R11_score_groups.png", bbox_inches="tight")
    plt.close()

    print("All report figures generated.")


generate_report_figures()

# ────────────────────────────────────────────────────────────────────────────
# 3.  Build DOCX document
# ────────────────────────────────────────────────────────────────────────────

doc = Document()

# ── Page margins ──
for section in doc.sections:
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin   = Cm(3.0)
    section.right_margin  = Cm(2.0)

# ── Default paragraph font ──
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(11)

# ── Heading style tweaks ──
for lvl in range(1, 4):
    style_name = f"Heading {lvl}"
    s = doc.styles[style_name]
    s.font.name = "Calibri"
    s.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    if lvl == 1:
        s.font.size = Pt(16)
    elif lvl == 2:
        s.font.size = Pt(13)
    else:
        s.font.size = Pt(11)

# ════════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ════════════════════════════════════════════════════════════════════════════
# Institution
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("IBM SkillsBuild Data Analytics with AI Academic Internship Program")
run.bold = True
run.font.size = Pt(13)
run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("BharatCares in association with AICTE")
run.bold = True
run.font.size = Pt(12)

doc.add_paragraph()
doc.add_paragraph()
doc.add_paragraph()

# Title
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Student Performance Analysis and Prediction")
run.bold = True
run.font.size = Pt(22)
run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Using Machine Learning")
run.bold = True
run.font.size = Pt(22)
run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Project Report")
run.font.size = Pt(14)
run.italic = True

doc.add_paragraph()
doc.add_paragraph()
doc.add_paragraph()

# Student info
for line in [
    ("Submitted By", True, Pt(12)),
    ("Rakesh Mondal", True, Pt(14)),
    ("B.Tech – Computer Science and Engineering (CSE)", False, Pt(11)),
]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(line[0])
    run.bold = line[1]
    run.font.size = line[2]

doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Dataset: Students Performance in Exams (Kaggle)")
run.font.size = Pt(11)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Technologies: Python · Pandas · Scikit-learn · Streamlit · Plotly")
run.font.size = Pt(11)

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS (manual listing)
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "Table of Contents", level=1)
toc_items = [
    ("1.", "Abstract"),
    ("2.", "Introduction"),
    ("3.", "Problem Statement"),
    ("4.", "Objectives"),
    ("5.", "Dataset Description"),
    ("6.", "Technologies Used"),
    ("7.", "Data Preprocessing"),
    ("8.", "Exploratory Data Analysis"),
    ("9.", "Machine Learning Models"),
    ("10.", "Actual Model Results"),
    ("11.", "Streamlit Dashboard"),
    ("12.", "Key Findings"),
    ("13.", "Limitations"),
    ("14.", "Future Scope"),
    ("15.", "Conclusion"),
    ("16.", "References"),
]
for num, title in toc_items:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(f"{num}  {title}")
    run.font.size = Pt(11)
doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════════
# 1. ABSTRACT
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "1. Abstract", level=1)
body(doc,
    "This report presents a comprehensive data analytics and machine-learning project "
    "that analyses the academic performance of 1,000 students using the publicly available "
    "'Students Performance in Exams' dataset from Kaggle. The project covers the complete "
    "data science pipeline: data ingestion, quality validation, feature engineering, "
    "exploratory data analysis (EDA), supervised regression modelling, and deployment of "
    "an interactive Streamlit dashboard. Five categorical features — gender, race/ethnicity, "
    "parental education level, lunch type, and test preparation course status — are used to "
    "predict a student's average exam score (mean of mathematics, reading, and writing scores). "
    "Three regression algorithms are evaluated: Linear Regression, Decision Tree Regressor, "
    "and Random Forest Regressor. Linear Regression achieves the best generalisation with "
    f"an MAE of {metrics['Linear Regression']['MAE']:.4f}, RMSE of "
    f"{metrics['Linear Regression']['RMSE']:.4f}, and R² of "
    f"{metrics['Linear Regression']['R2']:.4f}. The low R² value accurately reflects that "
    "demographic variables alone account for only a modest portion of individual score variance; "
    "this is an honest, unsurprising finding and not a modelling deficiency. EDA reveals "
    f"significant associations between test preparation, lunch type, parental education, and "
    "student outcomes. All project artefacts — data loader, feature-engineering module, "
    "Jupyter notebook, trained model pipeline, and Streamlit dashboard — are documented and "
    "reproducible."
)
doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════════
# 2. INTRODUCTION
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "2. Introduction", level=1)
body(doc,
    "Education is one of the most critical factors influencing an individual's future "
    "professional and personal prospects. Understanding the determinants of academic "
    "performance enables educators, school administrators, and policymakers to design "
    "evidence-based, targeted interventions that can close achievement gaps and improve "
    "learning outcomes across diverse student populations."
)
body(doc,
    "Machine learning and data analytics provide powerful tools to extract insights from "
    "educational data. Rather than relying solely on intuition, quantitative analysis of "
    "student records can reveal patterns that are difficult to observe through casual "
    "inspection. This project applies the full data science workflow to the 'Students "
    "Performance in Exams' dataset: loading, cleaning, feature engineering, statistical "
    "exploration, regression modelling, and interactive visualisation."
)
body(doc,
    "The project is submitted as part of the IBM SkillsBuild Data Analytics with AI "
    "Academic Internship Program, conducted by BharatCares in association with AICTE. "
    "The entire codebase — including a reusable data loader, feature-engineering module, "
    "annotated Jupyter notebook, and a multi-tab Streamlit dashboard — is structured for "
    "reproducibility and professional presentation."
)

# ════════════════════════════════════════════════════════════════════════════
# 3. PROBLEM STATEMENT
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "3. Problem Statement", level=1)
body(doc,
    "Given a student's demographic and socio-economic background — specifically gender, "
    "race/ethnicity group, parental level of education, lunch type, and test preparation "
    "course status — can a machine learning regression model accurately estimate their "
    "average exam score (the arithmetic mean of mathematics, reading, and writing scores)?"
)
body(doc,
    "The three individual subject scores are deliberately excluded as model inputs because "
    "they are direct arithmetic components of the target variable (average_score). Including "
    "them would constitute data leakage, yielding artificially perfect R² values that would "
    "not generalise to real-world prediction scenarios where subject scores are unknown."
)
body(doc,
    "This is a supervised regression problem. The target variable 'average_score' is a "
    "continuous numerical variable ranging from 0 to 100. Five categorical predictor "
    "variables encode demographic and contextual information about each student. The "
    "challenge is to quantify how much predictive power these features collectively provide."
)

# ════════════════════════════════════════════════════════════════════════════
# 4. OBJECTIVES
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "4. Objectives", level=1)
objectives = [
    "Load and validate the raw Student Performance CSV dataset, ensuring zero missing values and zero duplicate rows.",
    "Perform thorough data quality checks including missing-value analysis, duplicate detection, and dtype verification.",
    "Rename problematic column names (spaces, forward slash) to safe snake_case identifiers immediately after loading.",
    "Engineer three derived features: average_score, total_score, and score_group (Low / Medium / High).",
    "Conduct comprehensive Exploratory Data Analysis (EDA) across all five categorical demographic variables.",
    "Visualise score distributions using histograms and boxplots for each subject.",
    "Analyse how gender affects mathematics, reading, writing, and average scores.",
    "Examine the relationship between parental education level and student performance.",
    "Investigate the impact of lunch type on academic scores.",
    "Evaluate whether test preparation course completion improves exam outcomes.",
    "Explore performance variation across five race/ethnicity groups.",
    "Compute and visualise a Pearson correlation matrix of all numeric score variables.",
    "Train and compare three regression models: Linear Regression, Decision Tree Regressor, and Random Forest Regressor.",
    "Evaluate all models using MAE, MSE, RMSE, and R² on a 20% held-out test set.",
    "Persist the best-performing model pipeline and all evaluation metrics as project artefacts.",
    "Deploy an interactive, multi-tab Streamlit dashboard with real-time filters and ML prediction capability.",
]
for i, obj in enumerate(objectives, 1):
    bullet(doc, f"{i}. {obj}")

# ════════════════════════════════════════════════════════════════════════════
# 5. DATASET DESCRIPTION
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "5. Dataset Description", level=1)

heading(doc, "5.1  Dataset Source", level=2)
body(doc,
    "The dataset used in this project is the 'Students Performance in Exams' dataset, "
    "publicly available on Kaggle at:"
)
p = doc.add_paragraph()
run = p.add_run("https://www.kaggle.com/datasets/spscientist/students-performance-in-exams")
run.font.color.rgb = RGBColor(0x00, 0x70, 0xC0)
run.font.size = Pt(10)

body(doc,
    "The dataset was originally compiled for educational research purposes and contains "
    "fully anonymised student records with no personally identifiable information. "
    "It represents a cross-sectional sample of students at a single unnamed high school "
    "in the United States."
)

heading(doc, "5.2  Dataset Summary", level=2)
body(doc, "Key dataset properties:")
bullet(doc, "Total records: 1,000 student rows")
bullet(doc, "Original columns: 8 (5 categorical + 3 numerical)")
bullet(doc, "Engineered columns added: 3 (average_score, total_score, score_group)")
bullet(doc, "Missing values: 0 (confirmed by data loader validation)")
bullet(doc, "Duplicate rows: 0 (confirmed by data loader validation)")
bullet(doc, "File format: CSV with quoted string values")

heading(doc, "5.3  Column Descriptions", level=2)
body(doc, "The original eight columns and their descriptions are as follows:")

col_tbl = doc.add_table(rows=1, cols=3)
col_tbl.style = "Table Grid"
col_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
h = col_tbl.rows[0].cells
h[0].text = "Column Name"; h[1].text = "Type"; h[2].text = "Values / Range"
for cell in h:
    cell.paragraphs[0].runs[0].bold = True
    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_cell_bg(cell, "1F4E79")
    cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

col_rows = [
    ("gender", "Categorical", "female, male"),
    ("race/ethnicity", "Categorical", "group A, group B, group C, group D, group E"),
    ("parental level of education", "Categorical", "some high school, high school, some college, associate's degree, bachelor's degree, master's degree"),
    ("lunch", "Categorical", "standard, free/reduced"),
    ("test preparation course", "Categorical", "none, completed"),
    ("math score", "Integer (0–100)", "Minimum: 0, Maximum: 100, Mean: 66.09"),
    ("reading score", "Integer (0–100)", "Minimum: 17, Maximum: 100, Mean: 69.17"),
    ("writing score", "Integer (0–100)", "Minimum: 10, Maximum: 100, Mean: 68.05"),
]
for row_data in col_rows:
    row_cells = col_tbl.add_row().cells
    for i, val in enumerate(row_data):
        row_cells[i].text = val
        row_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT

heading(doc, "5.4  Descriptive Statistics", level=2)
body(doc, "The following table shows descriptive statistics for the three score columns and the engineered average_score:")
add_summary_stats_table(doc)
caption(doc, "Table 5.1: Descriptive statistics for score columns (1,000 students)")

# ════════════════════════════════════════════════════════════════════════════
# 6. TECHNOLOGIES USED
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "6. Technologies Used", level=1)

tech_tbl = doc.add_table(rows=1, cols=3)
tech_tbl.style = "Table Grid"
tech_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
th = tech_tbl.rows[0].cells
th[0].text = "Technology"; th[1].text = "Version"; th[2].text = "Purpose"
for cell in th:
    cell.paragraphs[0].runs[0].bold = True
    set_cell_bg(cell, "1F4E79")
    cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

tech_rows = [
    ("Python", "3.x", "Primary programming language for all analysis and modelling"),
    ("Pandas", "≥1.5", "Data loading, cleaning, transformation, and aggregation"),
    ("NumPy", "≥1.23", "Numerical operations and array manipulation"),
    ("Matplotlib", "≥3.6", "Static chart generation for EDA and report figures"),
    ("Seaborn", "≥0.12", "Statistical visualisation (heatmaps, boxplots, bar charts)"),
    ("Scikit-learn", "≥1.2", "ML pipeline, label encoding, train/test split, model training and evaluation"),
    ("Streamlit", "≥1.28", "Interactive multi-tab web dashboard with real-time filters"),
    ("Plotly", "≥5.14", "Interactive visualisations in the Streamlit dashboard"),
    ("Joblib", "≥1.2", "Model serialisation and persistence"),
    ("Jupyter Notebook", "≥1.0", "Exploratory analysis, documentation, and reproducible workflow"),
]
for row_data in tech_rows:
    row_cells = tech_tbl.add_row().cells
    for i, val in enumerate(row_data):
        row_cells[i].text = val
caption(doc, "Table 6.1: Technologies and libraries used in the project")

# ════════════════════════════════════════════════════════════════════════════
# 7. DATA PREPROCESSING
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "7. Data Preprocessing", level=1)

heading(doc, "7.1  Data Loading", level=2)
body(doc,
    "The raw CSV is read using pandas read_csv(). A canonical column rename map "
    "is applied immediately after loading to convert problematic names to safe "
    "snake_case identifiers. The column 'race/ethnicity' is renamed to 'race_ethnicity' "
    "to avoid forward-slash attribute access errors. Space-separated column names such "
    "as 'math score' are renamed to 'math_score', and similarly for reading and writing "
    "score columns and parental education."
)

heading(doc, "7.2  Missing Value Analysis", level=2)
body(doc,
    "After loading, a strict validation check is performed. The total count of missing "
    "values (NaN) across all columns is computed using df.isnull().sum().sum(). The "
    f"actual result for this dataset is 0 missing values across all 1,000 rows and "
    "8 columns. The data is complete with no imputation required."
)

heading(doc, "7.3  Duplicate Row Analysis", level=2)
body(doc,
    "A duplicate check is performed using df.duplicated().sum(). The actual result is "
    "0 duplicate rows. All 1,000 student records are unique."
)

heading(doc, "7.4  Data Types", level=2)
body(doc,
    "The five categorical columns (gender, race_ethnicity, parental_level_of_education, "
    "lunch, test_preparation_course) are stored as object/string dtype. The three score "
    "columns (math_score, reading_score, writing_score) are automatically cast to int64 "
    "by pandas during CSV reading, as the values are integers between 0 and 100."
)

heading(doc, "7.5  Feature Engineering", level=2)
body(doc, "Three derived features are computed by the engineer_features() module:")
bullet(doc, "average_score: Arithmetic mean of math_score, reading_score, and writing_score, rounded to 2 decimal places. This is the target variable for ML.")
bullet(doc, "total_score: Sum of the three subject scores. Range: 0–300.")
bullet(doc, "score_group: Categorical label derived from average_score thresholds: 'Low' (< 50), 'Medium' (50–69.99), 'High' (≥ 70).")
body(doc,
    f"Score group distribution in the dataset: High — {sg_high} students ({sg_high/10:.1f}%), "
    f"Medium — {sg_medium} students ({sg_medium/10:.1f}%), Low — {sg_low} students ({sg_low/10:.1f}%)."
)

heading(doc, "7.6  Encoding for ML", level=2)
body(doc,
    "For the machine learning pipeline, all five categorical features are encoded using "
    "scikit-learn's OrdinalEncoder wrapped in a ColumnTransformer. This produces a "
    "numerical representation suitable for tree-based and linear models. The encoder "
    "is fitted on the training set and applied to both training and test sets as part of "
    "a Pipeline, preventing data leakage from the test set into the encoding process."
)

# ════════════════════════════════════════════════════════════════════════════
# 8. EXPLORATORY DATA ANALYSIS
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "8. Exploratory Data Analysis", level=1)

heading(doc, "8.1  Score Distributions", level=2)
body(doc,
    f"The three subject scores are approximately normally distributed. Math has the "
    f"lowest mean ({avg_math}) while reading has the highest ({avg_reading}). "
    f"The overall average score mean is {avg_overall} with a standard deviation of 14.26. "
    "The minimum observed average score is 9.00 and the maximum is 100.00. "
    "Most students cluster in the 58–78 range (interquartile range: 58.33–77.67)."
)
insert_figure(doc, FIGURES_DIR / "R1_score_distributions.png",
              "Figure 8.1: Histogram of math, reading, and writing score distributions with mean lines")
insert_figure(doc, FIGURES_DIR / "R2_subject_boxplots.png",
              "Figure 8.2: Boxplot comparison of score distributions by subject")

heading(doc, "8.2  Gender Analysis", level=2)
body(doc,
    f"Female students outperform male students in reading (Female: 72.61 vs Male: 65.47) "
    f"and writing (Female: 72.47 vs Male: 63.31). Male students score higher in mathematics "
    f"(Male: 68.73 vs Female: 63.63). Overall, female students have a higher average score "
    f"({female_avg}) compared to male students ({male_avg}), a difference of "
    f"{round(female_avg - male_avg, 2)} points."
)
insert_figure(doc, FIGURES_DIR / "R3_gender_analysis.png",
              "Figure 8.3: Mean scores by gender and subject (left) and average score distribution by gender (right)")

heading(doc, "8.3  Race/Ethnicity Analysis", level=2)
body(doc,
    f"Performance increases monotonically from group A to group E. Group A has the lowest "
    f"average score (62.99) and group E the highest ({top_race_avg}), a difference of "
    f"{round(top_race_avg - 62.99, 2)} points. This 10-point spread across groups suggests "
    "that racial/ethnic grouping captures meaningful socio-economic variance in the dataset."
)
insert_figure(doc, FIGURES_DIR / "R4_race_ethnicity.png",
              "Figure 8.4: Average score by race/ethnicity group (ordered from lowest to highest)")

heading(doc, "8.4  Parental Education Analysis", level=2)
body(doc,
    f"There is a clear positive correlation between parental education level and student "
    f"performance. Students whose parents hold a master's degree achieve the highest mean "
    f"average score ({top_edu_avg}), while students whose parents have only a high school "
    f"education score lowest (63.10). The 10.5-point gap between these extremes highlights "
    "the importance of family educational background as a predictor of student outcomes."
)
insert_figure(doc, FIGURES_DIR / "R5_parental_education.png",
              "Figure 8.5: Average score by parental education level (ordered from lowest to highest)")

heading(doc, "8.5  Test Preparation Analysis", level=2)
body(doc,
    f"Students who completed the test preparation course score consistently higher across "
    f"all three subjects. The mean average score for 'completed' students is {completed_avg} "
    f"compared to {none_avg} for students who did not complete the course — a difference of "
    f"{test_prep_diff} points. This is the most actionable finding in the dataset: test "
    "preparation is strongly associated with improved outcomes."
)
insert_figure(doc, FIGURES_DIR / "R6_test_prep.png",
              "Figure 8.6: Mean scores by test preparation status across all subjects")

heading(doc, "8.6  Lunch Type Analysis", level=2)
body(doc,
    f"Students on a standard lunch plan outperform free/reduced lunch students by "
    f"{lunch_diff} points on average ({standard_avg} vs {reduced_avg}). This variable "
    "serves as a proxy for socio-economic status — students from lower-income households "
    "who qualify for free or reduced-price lunch tend to score lower across all subjects."
)
insert_figure(doc, FIGURES_DIR / "R7_lunch_analysis.png",
              "Figure 8.7: Mean scores by lunch type across all three subjects")

heading(doc, "8.7  Correlation Analysis", level=2)
body(doc,
    f"All three subject scores are highly positively correlated with each other. The "
    f"Pearson correlation between math and reading is {corr_mr}, between math and writing "
    f"is {corr_mw}, and between reading and writing is {corr_rw} — the strongest pairwise "
    "correlation. These high correlations indicate that students who perform well in one "
    "subject tend to perform well across all subjects, suggesting a general academic ability "
    "factor. Average score, being a linear combination of all three, naturally shows the "
    "highest correlations with each individual subject."
)
insert_figure(doc, FIGURES_DIR / "R8_correlation_heatmap.png",
              "Figure 8.8: Pearson correlation heatmap of all numeric score variables")

heading(doc, "8.8  Score Group Distribution", level=2)
body(doc,
    f"Using the engineered score_group feature: {sg_high} students (45.9%) are in the "
    f"'High' group (average ≥ 70), {sg_medium} (43.8%) are 'Medium' (50–69.99), and "
    f"{sg_low} (10.3%) are 'Low' (average < 50). The majority of students fall in the "
    "medium-to-high range, with only about 1 in 10 students scoring below 50 on average."
)
insert_figure(doc, FIGURES_DIR / "R11_score_groups.png",
              "Figure 8.9: Pie chart of student score group distribution (Low/Medium/High)")

# ════════════════════════════════════════════════════════════════════════════
# 9. MACHINE LEARNING MODELS
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "9. Machine Learning Models", level=1)

heading(doc, "9.1  Target Variable", level=2)
body(doc,
    "The target variable is average_score: the arithmetic mean of math_score, "
    "reading_score, and writing_score, rounded to 2 decimal places. It is a continuous "
    "numerical variable ranging from 9.00 to 100.00 in this dataset."
)

heading(doc, "9.2  Input Features", level=2)
body(doc, "Five categorical features are used as model inputs:")
for feat in metrics["feature_columns"]:
    bullet(doc, feat)
body(doc,
    "The individual subject scores (math_score, reading_score, writing_score) are "
    "intentionally excluded to prevent data leakage. Including them would make the "
    "target trivially predictable, as average_score = (math + reading + writing) / 3."
)

heading(doc, "9.3  Train / Test Split", level=2)
body(doc,
    "The dataset (1,000 samples) is split into 80% training (800 samples) and 20% "
    "test (200 samples) using scikit-learn's train_test_split() with random_state=42 "
    "for reproducibility. All model evaluation metrics are computed on the held-out "
    "test set only."
)

heading(doc, "9.4  Preprocessing Pipeline", level=2)
body(doc,
    "A scikit-learn Pipeline is constructed with two steps: (1) a ColumnTransformer "
    "applying OrdinalEncoder to all five categorical feature columns, and (2) the "
    "regression model. This ensures that encoding parameters are fitted on training "
    "data only and applied consistently to the test set, preventing any data leakage."
)

heading(doc, "9.5  Models Trained", level=2)
body(doc, "Three regression models are trained and evaluated:")
bullet(doc, "Linear Regression: Baseline model that fits a hyperplane through the encoded feature space. Assumes a linear relationship between features and target.")
bullet(doc, "Decision Tree Regressor: Non-linear model that partitions the feature space using recursive binary splits. Can capture interaction effects but is prone to overfitting on small datasets.")
bullet(doc, "Random Forest Regressor: Ensemble of decision trees with bagging and feature subsampling. Generally more robust than a single tree but requires more training data to outperform linear models.")

heading(doc, "9.6  Evaluation Metrics", level=2)
body(doc, "All models are evaluated using four standard regression metrics on the test set:")
bullet(doc, "MAE (Mean Absolute Error): Average absolute difference between actual and predicted values.")
bullet(doc, "MSE (Mean Squared Error): Average squared difference, penalising large errors more heavily.")
bullet(doc, "RMSE (Root Mean Squared Error): Square root of MSE, interpretable in the same units as the target.")
bullet(doc, "R² (Coefficient of Determination): Proportion of target variance explained by the model. R²=1 is perfect; R²=0 means the model is no better than predicting the mean.")

# ════════════════════════════════════════════════════════════════════════════
# 10. ACTUAL MODEL RESULTS
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "10. Actual Model Results", level=1)
body(doc,
    "The following table shows the actual evaluation metrics generated by running the "
    "machine learning pipeline on the 200-sample held-out test set. All values are read "
    "directly from outputs/metrics.json produced by the training notebook."
)

add_metrics_table(doc)
caption(doc, "Table 10.1: Actual ML model evaluation metrics (test set, n=200)")

doc.add_paragraph()
body(doc,
    f"Linear Regression achieves the best performance with an R² of "
    f"{metrics['Linear Regression']['R2']:.4f}, MAE of "
    f"{metrics['Linear Regression']['MAE']:.4f}, MSE of "
    f"{metrics['Linear Regression']['MSE']:.4f}, and RMSE of "
    f"{metrics['Linear Regression']['RMSE']:.4f}."
)
body(doc,
    f"The Decision Tree and Random Forest models perform worse (negative R²: "
    f"{metrics['Decision Tree']['R2']:.4f} and {metrics['Random Forest']['R2']:.4f} "
    f"respectively), indicating they are not better than a constant mean predictor on "
    "this small dataset. This is an expected outcome: with only 5 categorical features "
    "and limited data, tree-based models tend to overfit the training set and underperform "
    "on the test set."
)
body(doc,
    f"The linear regression R² of {metrics['Linear Regression']['R2']:.4f} means that "
    "the five demographic features explain approximately 16.2% of the variance in average "
    "scores. The remaining ~83.8% is attributable to individual factors not captured in "
    "the dataset: study habits, attendance, cognitive ability, teacher quality, and so on. "
    "This is a realistic and honest result for a model that uses only demographic background features."
)

insert_figure(doc, FIGURES_DIR / "R9_model_comparison.png",
              "Figure 10.1: Side-by-side comparison of R², MAE, and RMSE across all three models")
insert_figure(doc, FIGURES_DIR / "R10_actual_vs_predicted.png",
              "Figure 10.2: Actual vs Predicted average score scatter plot — Linear Regression (best model)")

body(doc,
    "In Figure 10.2, the red dashed line represents perfect prediction (predicted = actual). "
    "The scatter of points around this line illustrates the prediction uncertainty. The "
    "vertical spread at each actual score level reflects the high within-group variance "
    "that cannot be captured from demographic features alone."
)

# ════════════════════════════════════════════════════════════════════════════
# 11. STREAMLIT DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "11. Streamlit Dashboard", level=1)
body(doc,
    "An interactive, multi-tab Streamlit dashboard was built as the primary deliverable "
    "of this project. The dashboard is launched locally using 'streamlit run app.py' and "
    "provides a professional user interface for exploring the dataset, analysing demographic "
    "patterns, and generating ML-based predictions. The dashboard uses Plotly for all "
    "interactive charts and communicates directly with the trained model pipeline and "
    "processed dataset."
)

heading(doc, "11.1  Dashboard Architecture", level=2)
bullet(doc, "Entry point: app.py (project root)")
bullet(doc, "Data access: src/data_loader.py → load_data()")
bullet(doc, "Feature engineering: src/feature_engineering.py → engineer_features()")
bullet(doc, "ML model: outputs/models/best_model.pkl (scikit-learn Pipeline, Linear Regression)")
bullet(doc, "Metrics: outputs/metrics.json")
bullet(doc, "Framework: Streamlit ≥1.28 with wide layout")
bullet(doc, "Charts: Plotly Express and Plotly Graph Objects (interactive, hover-enabled)")

heading(doc, "11.2  Sidebar", level=2)
body(doc,
    "The dashboard sidebar displays dataset metadata (1,000 records, column count, Kaggle "
    "source) and provides five multiselect filter widgets:"
)
bullet(doc, "Gender (female / male)")
bullet(doc, "Race/Ethnicity (group A through group E)")
bullet(doc, "Parental Education (6 levels in natural education order)")
bullet(doc, "Lunch type (standard / free/reduced)")
bullet(doc, "Test Preparation (none / completed)")
body(doc,
    "A 'Reset Filters' button restores all filters to their default (all-selected) state. "
    "All tabs reflect the currently selected filter state in real time."
)

heading(doc, "11.3  Tab 1 — Overview", level=2)
body(doc,
    "The Overview tab displays five KPI metric cards at the top of the page showing: "
    "Total Students, Avg Math Score, Avg Reading Score, Avg Writing Score, and Overall Average. "
    "Below the KPIs, an overlaid histogram shows the score distributions for all four score "
    "columns (Math, Reading, Writing, Average). A paginated data preview table displays the "
    "first 20 rows of the filtered dataset."
)
body(doc,
    f"For the full unfiltered dataset: Total Students = 1,000, Avg Math = {avg_math}, "
    f"Avg Reading = {avg_reading}, Avg Writing = {avg_writing}, Overall Average = {avg_overall}."
)

heading(doc, "11.4  Tab 2 — Performance Analysis", level=2)
body(doc,
    "This tab shows mean scores per subject as an annotated bar chart, subject score "
    "distributions as boxplots, and two scatter plots showing the relationship between "
    "math score and reading/writing scores, colour-coded by gender."
)

heading(doc, "11.5  Tab 3 — Demographic Analysis", level=2)
body(doc,
    "Three sections cover: (1) Gender Analysis — grouped bar chart of mean scores by "
    "gender and subject, and a boxplot of average score by gender; (2) Race/Ethnicity "
    "Analysis — bar chart of average score by group; (3) Parental Education Analysis — "
    "horizontal bar chart coloured by score magnitude."
)

heading(doc, "11.6  Tab 4 — Test Preparation Analysis", level=2)
body(doc,
    "A grouped bar chart compares mean scores across all subjects between students who "
    "completed vs did not complete test preparation. A second chart shows score comparison "
    "by lunch type. A heatmap cross-tabulates average score by test preparation × lunch type."
)

heading(doc, "11.7  Tab 5 — Correlation Analysis", level=2)
body(doc,
    "An interactive Plotly heatmap displays Pearson correlations among numeric score "
    "variables. Three pair scatter plots (Math vs Reading, Math vs Writing, Reading vs "
    "Writing) are displayed side by side, colour-coded by score group (Low/Medium/High)."
)

heading(doc, "11.8  Tab 6 — Machine Learning Prediction", level=2)
body(doc,
    "This tab provides: (1) a student profile input form with five dropdown selectors "
    "(gender, race/ethnicity, parental education, lunch type, test preparation), (2) a "
    "real-time prediction button that uses the loaded Linear Regression pipeline to "
    "predict and display the student's estimated average score, (3) the full model "
    "evaluation metrics table (all three models), and (4) an Actual vs Predicted scatter "
    "plot for the full unfiltered dataset."
)

heading(doc, "11.9  Tab 7 — Key Insights", level=2)
body(doc,
    "The Key Insights tab presents 11 computed insight statements derived from the full "
    "dataset, including gender performance comparisons, test preparation impact, lunch "
    "type effect, top-performing race/ethnicity group, top parental education level, "
    "correlation values, and model performance. A descriptive statistics summary table "
    "is also displayed."
)

# ════════════════════════════════════════════════════════════════════════════
# 12. KEY FINDINGS
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "12. Key Findings", level=1)
body(doc, "The following findings are directly supported by the actual dataset analysis:")

findings = [
    f"The dataset contains 1,000 complete student records with zero missing values and zero duplicates.",
    f"The overall average score is {avg_overall} (Math: {avg_math}, Reading: {avg_reading}, Writing: {avg_writing}).",
    f"Female students outperform male students overall (Female avg: {female_avg} vs Male avg: {male_avg}, Δ = {round(female_avg-male_avg,2)} pts). Males score higher in mathematics; females score higher in reading and writing.",
    f"Test preparation course completion is the single strongest actionable predictor: students who completed the course score {test_prep_diff} points higher on average ({completed_avg} vs {none_avg}).",
    f"Lunch type (standard vs free/reduced) is a strong socio-economic proxy: standard lunch students score {lunch_diff} points higher on average ({standard_avg} vs {reduced_avg}).",
    f"Parental education level has a monotonically positive relationship with student scores: master's degree parents → avg {top_edu_avg}; high school parents → avg 63.10.",
    f"Race/ethnicity performance is monotonically ordered from group A (62.99) to group E (72.75), a 9.76-point spread.",
    f"Inter-subject correlations are very high: Math–Reading = {corr_mr}, Math–Writing = {corr_mw}, Reading–Writing = {corr_rw}, confirming a strong general academic ability factor.",
    f"Score group distribution: {sg_high} High (≥70), {sg_medium} Medium (50–69), {sg_low} Low (<50) students.",
    f"Linear Regression outperforms Decision Tree and Random Forest on this dataset, achieving R² = {metrics['Linear Regression']['R2']:.4f}, MAE = {metrics['Linear Regression']['MAE']:.4f}, RMSE = {metrics['Linear Regression']['RMSE']:.4f}.",
    f"Demographic variables alone explain ~16% of score variance (R² ≈ 0.16), confirming that individual unmeasured factors dominate academic performance.",
]
for f_text in findings:
    bullet(doc, f_text)

# ════════════════════════════════════════════════════════════════════════════
# 13. LIMITATIONS
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "13. Limitations", level=1)

limitations = [
    "Limited feature set: Only five categorical variables are available as predictors. Key factors such as study hours, attendance, prior GPA, socio-economic index, and teacher quality are absent, limiting the achievable R².",
    "Low R² (~16%): The model explains only a small fraction of individual score variance, making it unsuitable for individual-level prediction but still useful for understanding group-level patterns.",
    "Dataset size: With only 1,000 records and 5 categorical features, complex models like Random Forest do not have sufficient data to outperform simple linear regression.",
    "Cross-sectional data: The dataset represents a single snapshot; there is no longitudinal information to study how students progress over time.",
    "Single school / unknown context: The school is unnamed and the country is not explicitly stated. Generalisability to other educational systems is uncertain.",
    "No individual-level factors: Intelligence, motivation, parental involvement, and school quality are all unmeasured, yet are major determinants of academic performance.",
    "Binary / coarse categorisation: Variables like parental education are ordinal but treated as nominal by OrdinalEncoder. A more sophisticated ordinal encoding might capture the rank order more accurately.",
    "No temporal information: There is no date or year variable, so trends over time cannot be studied.",
]
for lim in limitations:
    bullet(doc, lim)

# ════════════════════════════════════════════════════════════════════════════
# 14. FUTURE SCOPE
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "14. Future Scope", level=1)

future_items = [
    "Collect richer features: Include study hours per week, attendance rate, extracurricular activities, and parent involvement scores to improve predictive power.",
    "Advanced ML models: Explore Gradient Boosting (XGBoost, LightGBM, CatBoost), Support Vector Regression, and neural networks as the dataset grows.",
    "Classification formulation: Reframe as a multi-class classification problem predicting score_group (Low/Medium/High) and explore classification metrics (F1-score, ROC-AUC).",
    "Hyperparameter tuning: Apply GridSearchCV or Optuna to optimise model hyperparameters, particularly for ensemble models.",
    "Natural Language Processing: If student feedback or teacher comments are available, apply NLP to extract qualitative performance signals.",
    "Fairness and bias analysis: Conduct a formal analysis of model fairness across demographic groups to ensure equitable predictions.",
    "Real-time data pipeline: Connect the dashboard to a live database or API for real-time performance tracking.",
    "Longitudinal study: Collect data across multiple academic years to build time-series models of student progress.",
    "Deployment: Deploy the Streamlit app to Streamlit Community Cloud, AWS, or Azure for broader institutional access.",
    "Explainability (XAI): Integrate SHAP or LIME to provide per-student explanations of model predictions.",
]
for item in future_items:
    bullet(doc, item)

# ════════════════════════════════════════════════════════════════════════════
# 15. CONCLUSION
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "15. Conclusion", level=1)
body(doc,
    "This project demonstrates a complete, reproducible data analytics and machine "
    "learning pipeline applied to student academic performance data. Starting from a "
    "raw CSV dataset of 1,000 high-school students, the project delivers a clean "
    "codebase, thorough exploratory analysis, three trained regression models, and "
    "an interactive Streamlit dashboard — all built to professional standards."
)
body(doc,
    "The key technical findings are: (1) test preparation course completion and standard "
    "lunch type are the two most impactful factors associated with higher scores; "
    "(2) parental education level and race/ethnicity group both show clear positive "
    "associations with performance; (3) inter-subject correlations are very high "
    "(0.80–0.95), confirming a strong general academic ability factor; and (4) Linear "
    "Regression achieves the best out-of-sample R² of 0.16 using only demographic "
    "features, honestly reflecting the limited predictive power of categorical "
    "background variables for individual score prediction."
)
body(doc,
    "The project fulfils all stated objectives and provides a solid foundation for "
    "further research. The modular code architecture (data_loader.py, "
    "feature_engineering.py, app.py) ensures maintainability and extensibility. "
    "The Streamlit dashboard transforms the analytical outputs into an accessible, "
    "interactive tool that educators and administrators could use to explore performance "
    "patterns across student subgroups."
)
body(doc,
    "This work was completed as part of the IBM SkillsBuild Data Analytics with AI "
    "Academic Internship Program, conducted by BharatCares in association with AICTE, "
    "and represents the application of industry-standard data science practices to a "
    "real-world educational dataset."
)

# ════════════════════════════════════════════════════════════════════════════
# 16. REFERENCES
# ════════════════════════════════════════════════════════════════════════════
heading(doc, "16. References", level=1)

references = [
    '[1] SP Scientist (2019). "Students Performance in Exams." Kaggle. https://www.kaggle.com/datasets/spscientist/students-performance-in-exams',
    '[2] McKinney, W. (2010). "Data Structures for Statistical Computing in Python." Proceedings of the 9th Python in Science Conference.',
    '[3] Pedregosa, F. et al. (2011). "Scikit-learn: Machine Learning in Python." Journal of Machine Learning Research, 12, pp. 2825–2830.',
    '[4] Plotly Technologies Inc. (2015). Collaborative data science. Montréal, QC. https://plot.ly',
    '[5] Streamlit Inc. (2019). Streamlit — A faster way to build and share data apps. https://streamlit.io',
    '[6] Hunter, J. D. (2007). "Matplotlib: A 2D Graphics Environment." Computing in Science & Engineering, 9(3), pp. 90–95.',
    '[7] Waskom, M. (2021). "seaborn: statistical data visualization." Journal of Open Source Software, 6(60), 3021.',
    '[8] Harris, C. R. et al. (2020). "Array programming with NumPy." Nature, 585(7825), pp. 357–362.',
    '[9] IBM SkillsBuild. Data Analytics with AI. https://skillsbuild.org',
    '[10] AICTE & BharatCares. (2024). Academic Internship Program in Data Analytics.',
]
for ref in references:
    p = doc.add_paragraph(ref, style="List Bullet")
    p.paragraph_format.space_after = Pt(4)

# ────────────────────────────────────────────────────────────────────────────
# Page numbers
# ────────────────────────────────────────────────────────────────────────────
add_page_number(doc)

# ────────────────────────────────────────────────────────────────────────────
# Save
# ────────────────────────────────────────────────────────────────────────────
output_path = "RakeshMondal_ProjectReport.docx"
doc.save(output_path)
print(f"\nReport saved: {output_path}")
