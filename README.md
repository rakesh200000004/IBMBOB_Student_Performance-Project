# 🎓 Student Performance Analysis and Prediction Using Machine Learning

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)
![License](https://img.shields.io/badge/License-Academic-green)

**IBM SkillsBuild Data Analytics with AI Academic Internship**
BharatCares in association with AICTE
**Student:** Rakesh Mondal | B.Tech CSE

---

## 2. Project Overview

This project performs end-to-end analysis and machine learning on a dataset of 1,000 student exam
records to explore how demographic and socioeconomic factors relate to academic performance.
Using Python, Jupyter Notebook, and Scikit-learn, the project applies exploratory data analysis
(EDA), feature engineering, and regression modelling to predict a student's average score from
five categorical background attributes. An interactive Streamlit dashboard is also provided so
users can filter the data visually and obtain live model predictions through an easy-to-use web
interface.

---

## 3. Problem Statement

Student exam outcomes are influenced by a range of background factors including gender,
race/ethnicity, parental level of education, lunch type, and completion of a test preparation
course. Understanding the associations between these factors and academic scores can help
educators and policymakers identify groups that may benefit from additional support. This project
analyses those associations using statistical exploration and builds honest, leakage-free
regression models to quantify the predictive power of categorical background variables alone —
without claiming causal relationships.

---

## 4. Objectives

1. Load and validate the raw dataset, confirming no missing values or duplicate records.
2. Rename the `race/ethnicity` column to `race_ethnicity` to avoid forward-slash issues downstream.
3. Cast score columns to numeric types and verify the resulting data types.
4. Engineer three derived columns: `average_score`, `total_score`, and `score_group`.
5. Conduct exploratory data analysis across gender, race/ethnicity, parental education, lunch type, and test preparation.
6. Visualise score distributions using histograms, KDE plots, and boxplots.
7. Examine pairwise correlations between numeric score columns using a heatmap.
8. Encode all five categorical features with OneHotEncoder inside a Scikit-learn Pipeline to prevent leakage.
9. Split the dataset 80/20 (train/test) with `random_state=42` for reproducibility.
10. Train and evaluate Linear Regression, Decision Tree Regressor, and Random Forest Regressor.
11. Compare all three models using MAE, MSE, RMSE, and R² metrics.
12. Save the best-performing model pipeline to `outputs/models/best_model.pkl`.
13. Export all metrics to `outputs/metrics.json` for reuse in the dashboard and report.
14. Build an interactive seven-tab Streamlit dashboard with live filtering and a prediction widget.

---

## 5. Dataset Information

| Column | Type | Description | Values |
|---|---|---|---|
| `gender` | Categorical | Student's gender | `female`, `male` |
| `race/ethnicity` | Categorical | Student's racial/ethnic group | `group A`, `group B`, `group C`, `group D`, `group E` |
| `parental level of education` | Categorical | Highest education level of parent/guardian | `some high school`, `high school`, `some college`, `associate's degree`, `bachelor's degree`, `master's degree` |
| `lunch` | Categorical | Type of lunch the student receives | `standard`, `free/reduced` |
| `test preparation course` | Categorical | Whether the student completed a test prep course | `none`, `completed` |
| `math score` | Numeric (int) | Exam score in mathematics | 0–100 |
| `reading score` | Numeric (int) | Exam score in reading | 0–100 |
| `writing score` | Numeric (int) | Exam score in writing | 0–100 |

---

## 6. Kaggle Dataset Link

**Source:** [Students Performance in Exams — Kaggle](https://www.kaggle.com/datasets/spscientist/students-performance-in-exams)

---

## 7. Technologies Used

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.8+ | Core programming language |
| Pandas | ≥ 1.5 | Data loading, cleaning, and manipulation |
| NumPy | ≥ 1.23 | Numerical operations and array handling |
| Matplotlib | ≥ 3.6 | Static chart rendering in the notebook |
| Seaborn | ≥ 0.12 | Statistical visualisations (boxplots, heatmaps) |
| Scikit-learn | ≥ 1.2 | ML pipelines, encoding, models, and metrics |
| Streamlit | ≥ 1.28 | Interactive web dashboard |
| Plotly | ≥ 5.14 | Interactive charts inside the Streamlit dashboard |
| Joblib | ≥ 1.2 | Saving and loading the trained model pipeline |
| Jupyter | ≥ 1.0 | Interactive notebook environment |
| NBConvert | ≥ 7.0 | Programmatic notebook execution and export |

---

## 8. Project Workflow

1. **Data Collection** — Load `StudentsPerformance.csv` (1,000 rows × 8 columns) from the project root using `src/data_loader.py`.
2. **Data Validation** — Confirm zero missing values and zero duplicate rows; rename `race/ethnicity` to `race_ethnicity`.
3. **Feature Engineering** — Compute `average_score`, `total_score`, and `score_group` (Low / Medium / High) via `src/feature_engineering.py`.
4. **Exploratory Data Analysis** — Visualise score distributions, demographic comparisons, and inter-subject correlations across 12+ charts.
5. **Feature Selection** — Select the five categorical columns as input features; exclude the three raw score columns to prevent data leakage.
6. **Preprocessing Pipeline** — Apply `OneHotEncoder` inside a `ColumnTransformer` wrapped in a Scikit-learn `Pipeline`, fit only on the training split.
7. **Train/Test Split** — Divide data 80/20 with `random_state=42`.
8. **Model Training** — Train Linear Regression, Decision Tree Regressor, and Random Forest Regressor.
9. **Model Evaluation** — Score all models with MAE, MSE, RMSE, and R²; export results to `outputs/metrics.json`.
10. **Model Persistence** — Serialise the best-performing pipeline to `outputs/models/best_model.pkl` with Joblib.
11. **Dashboard Deployment** — Serve the interactive Streamlit app (`app.py`) with live filters and a prediction interface.

---

## 9. EDA Highlights

- Students who completed the test preparation course consistently score higher across all three subjects compared to those who did not.
- Students receiving a standard lunch type outperform those on free/reduced lunch in all three exam areas, with mean differences above 10 points.
- Parental level of education shows a positive gradient: students whose parents hold a bachelor's or master's degree tend to achieve higher average scores than those from lower parental-education backgrounds.
- Math score distributions differ by gender, with male students scoring relatively higher in math and female students scoring somewhat higher in reading and writing.
- Race/ethnicity group E records the highest mean scores among all groups, while group A records the lowest, though all groups overlap substantially.
- The three subject scores (math, reading, writing) are highly correlated with each other (above 0.80), indicating that students who perform well in one subject tend to perform well in others.
- The majority of students (High + Medium score groups) achieve average scores above 60, while the Low group (≈10% of students) averages below 45.
- Score distributions are approximately bell-shaped for all three subjects, with slight left skew in reading and writing.

---

## 10. Machine Learning

**Target variable:** `average_score` — arithmetic mean of `math score`, `reading score`, and `writing score`, computed before the train/test split.

**Input features (5 categorical):**

| Feature | Encoding |
|---|---|
| `gender` | OneHotEncoder (via Pipeline) |
| `race_ethnicity` | OneHotEncoder (via Pipeline) |
| `parental_level_of_education` | OneHotEncoder (via Pipeline) |
| `lunch` | OneHotEncoder (via Pipeline) |
| `test_preparation_course` | OneHotEncoder (via Pipeline) |

**Why subject scores are excluded:** `math score`, `reading score`, and `writing score` are the
direct arithmetic components of `average_score`. Including them as features would cause data
leakage — the model would trivially reconstruct the target and produce inflated, unrealistic
metrics. They are intentionally excluded to produce an honest benchmark.

**Models compared:** Linear Regression, Decision Tree Regressor, Random Forest Regressor

**Split:** 80% training / 20% test, `random_state=42`

**Pipeline:** `ColumnTransformer` (OneHotEncoder, `handle_unknown='ignore'`) → Regressor

---

## 11. Model Evaluation Results

| Model | MAE | MSE | RMSE | R² |
|---|---|---|---|---|
| Linear Regression | 10.49 | 179.61 | 13.40 | 0.1622 |
| Decision Tree | 11.87 | 231.94 | 15.23 | −0.0819 |
| Random Forest | 11.49 | 219.82 | 14.83 | −0.0254 |

**Best Model:** Linear Regression (R² = 0.1622)

> **Note:** The modest R² values are expected because the model uses only 5 categorical features.
> Subject scores are intentionally excluded to prevent data leakage. The goal is a leakage-free,
> honest benchmark.

---

## 12. Streamlit Dashboard

The dashboard is structured across **seven tabs** with a reactive sidebar:

**Sidebar filters** — Multiselect widgets for Gender, Race/Ethnicity, Parental Education, Lunch
Type, and Test Preparation Course. All charts update reactively when filters change. Dataset row
and column counts are displayed at the top of the sidebar.

| Tab | Content |
|---|---|
| **Overview** | 5 KPI metric cards (Total Students, Avg Math, Avg Reading, Avg Writing, Overall Average); overlaid score-distribution histogram; data preview table |
| **Performance Analysis** | Subject-wise mean bar chart; score boxplots; scatter plots (Math vs Reading, Math vs Writing, Reading vs Writing) |
| **Demographic Analysis** | Gender comparison grouped bar; Race/Ethnicity mean score bar; Parental Education horizontal bar |
| **Test Preparation Analysis** | Test prep vs no-prep grouped bar (all three subjects); lunch-type comparison; combined test prep × lunch cross-tab |
| **Correlation Analysis** | Numeric correlation heatmap; scatter matrix for pairwise subject relationships |
| **Machine Learning Prediction** | Five selectboxes for model input; "Predict Average Score" button; predicted score display with disclaimer; model metrics table; Actual vs Predicted scatter chart |
| **Key Insights** | Bullet-point EDA findings; dataset summary statistics table |

---

## 13. How to Install

```bash
# Clone or download the project
# Navigate to the project folder
pip install -r requirements.txt
```

---

## 14. How to Run

### Run the Jupyter Notebook

```bash
jupyter notebook RakeshMondal_StudentPerformance.ipynb
```

### Run the Streamlit Dashboard

```bash
streamlit run app.py
```

---

## 15. Project File Structure

```
Student_Performance_AI_Project/
├── StudentsPerformance.csv
├── RakeshMondal_StudentPerformance.ipynb
├── app.py
├── requirements.txt
├── README.md
├── RakeshMondal_ProjectReport.docx
├── src/
│   ├── __init__.py
│   ├── data_loader.py
│   └── feature_engineering.py
├── data/
│   └── processed/
└── outputs/
    ├── figures/       # 12 PNG visualisations
    ├── models/
    │   └── best_model.pkl
    └── metrics.json
```

---

## 16. Limitations

- Only five categorical variables are available as model features; continuous or ordinal predictors such as study hours, attendance rate, or household income are absent from the dataset.
- R² values are modest (≤ 0.16) because categorical demographic features alone explain a limited share of variance in exam scores.
- No causal claims can be made — all findings are associative; confounding variables are not controlled for.
- The dataset contains 1,000 records from a single source; results may not generalise to broader student populations or different educational systems.
- The three regression models are evaluated without extensive hyperparameter tuning; more systematic search (e.g., GridSearchCV) could yield better-optimised baselines.
- The dashboard requires local Python and Streamlit installation; it is not hosted on a public server.

---

## 17. Future Scope

- Incorporate richer features such as study hours per week, class attendance, extracurricular activities, and socioeconomic indicators to improve predictive power.
- Experiment with additional models including Gradient Boosting (XGBoost, LightGBM), Support Vector Regression, and neural network regressors.
- Apply systematic hyperparameter tuning via `GridSearchCV` or `RandomizedSearchCV` for all candidate models.
- Extend from regression to multi-class classification (Low / Medium / High performance) to explore alternative framings of the problem.
- Collect longitudinal data across multiple years to study performance trends and enable time-series analysis.
- Deploy the Streamlit dashboard to a cloud platform (Streamlit Community Cloud, Heroku, or AWS) for public access.
- Integrate SHAP (SHapley Additive exPlanations) values to provide interpretable per-prediction feature attributions.
- Add multilingual support to make the dashboard accessible to non-English-speaking educators and parents.

---

## 18. Author

**Rakesh Mondal**
B.Tech in Computer Science Engineering
IBM SkillsBuild Data Analytics with AI Academic Internship
BharatCares in association with AICTE
