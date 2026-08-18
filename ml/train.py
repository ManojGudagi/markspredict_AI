import os
import joblib
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# =========================================================
# STEP 1: LOAD CSV DATASET
# =========================================================

dataset_path = os.path.join(
    BASE_DIR,
    "ml",
    "datasets",
    "student_marks.csv"
)

if not os.path.exists(dataset_path):
    dataset_path = os.path.join(BASE_DIR, "data.csv")

print(f"Loading dataset from: {dataset_path}")
df = pd.read_csv(dataset_path)

# =========================================================
# STEP 2: PREPROCESSING & VALIDATION
# =========================================================

# 1. Normalize Column Names & Check Required Headers
if "assignments_score" in df.columns and "assignments" not in df.columns:
    df.rename(columns={"assignments_score": "assignments"}, inplace=True)

required_columns = [
    "study_hours",
    "attendance",
    "previous_marks",
    "assignments",
    "final_marks",
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

# 2. Remove Duplicates
initial_rows = len(df)
df = df.drop_duplicates()
if len(df) < initial_rows:
    print(f"Removed {initial_rows - len(df)} duplicate row(s).")

# 3. Handle Missing Values & Convert Numerical Data
numeric_columns = [
    col for col in [
        "study_hours",
        "attendance",
        "previous_marks",
        "assignments",
        "internal_marks",
        "final_marks",
    ]
    if col in df.columns
]

df[numeric_columns] = df[numeric_columns].apply(
    pd.to_numeric,
    errors="coerce"
)

rows_before_na = len(df)
df = df.dropna(subset=numeric_columns)
if len(df) < rows_before_na:
    print(f"Dropped {rows_before_na - len(df)} invalid/missing row(s).")

# 4. Range Validation
if (df["study_hours"] < 0).any():
    raise ValueError("Study hours cannot be negative.")

if not df["attendance"].between(0, 100).all():
    raise ValueError("Attendance must be between 0 and 100.")

for col in ["previous_marks", "final_marks"]:
    if not df[col].between(0, 100).all():
        raise ValueError(
            f"{col} must contain values between 0 and 100."
        )

if (df["assignments"] < 0).any():
    raise ValueError("Assignments cannot be negative.")

if "internal_marks" in df.columns:
    if not df["internal_marks"].between(0, 100).all():
        raise ValueError("Internal marks must contain values between 0 and 100.")

print(f"Dataset preprocessed successfully! ({len(df)} valid records)")

# =========================================================
# STEP 3: TRAIN / TEST SPLIT
# =========================================================

features = [
    "study_hours",
    "attendance",
    "previous_marks",
    "assignments",
]

target = "final_marks"

X = df[features]
y = df[target]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# =========================================================
# STEP 4: CANDIDATE MODELS & 5-FOLD CROSS-VALIDATION
# =========================================================

models = {
    "Linear Regression": LinearRegression(),
    "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
}

results = {}
best_model = None
best_model_name = ""
best_score = -float("inf")
best_metrics = {}

print("\nStarting model evaluation & 5-fold cross-validation...")

for name, model in models.items():
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    cv_mean = float(np.mean(cv_scores))
    cv_std = float(np.std(cv_scores))

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    print(f"\n--- {name} ---")
    print(f"Test MAE   : {mae:.2f}")
    print(f"Test MSE   : {mse:.2f}")
    print(f"Test RMSE  : {rmse:.2f}")
    print(f"Test R2    : {r2:.4f}")
    print(f"5-Fold CV R2 Mean : {cv_mean:.4f} (±{cv_std:.4f})")

    metrics = {
        "mae": round(float(mae), 4),
        "mse": round(float(mse), 4),
        "rmse": round(float(rmse), 4),
        "r2_score": round(float(r2), 4),
        "cv_mean": round(cv_mean, 4),
        "cv_std": round(cv_std, 4),
    }

    results[name] = metrics

    combined_score = (r2 + cv_mean) / 2
    if combined_score > best_score:
        best_score = combined_score
        best_model_name = name
        best_model = model
        best_metrics = metrics

print("\n======================================")
print("BEST MODEL SELECTED")
print("======================================")
print(f"Model        : {best_model_name}")
print(f"Test R2      : {best_metrics['r2_score']:.4f}")
print(f"5-Fold CV Mean: {best_metrics['cv_mean']:.4f}")
print("======================================\n")

ml_dir = os.path.join(BASE_DIR, "ml")
os.makedirs(ml_dir, exist_ok=True)

# =========================================================
# STEP 5: SAVE ML ARTIFACTS
# =========================================================

# 1. Best Model
model_path = os.path.join(ml_dir, "model.pkl")
joblib.dump(best_model, model_path)
print(f"Best model saved to:\n{model_path}")

# 2. Best Model Metrics
metrics_path = os.path.join(ml_dir, "metrics.pkl")
joblib.dump(best_metrics, metrics_path)
print(f"Metrics saved to:\n{metrics_path}")

# 3. Model Comparison (with 5-Fold CV stats)
comparison_path = os.path.join(ml_dir, "model_comparison.pkl")
comparison_data = {
    "models": results,
    "best_model": best_model_name
}
joblib.dump(comparison_data, comparison_path)
print(f"Model comparison saved to:\n{comparison_path}")

# 4. Evaluation Data (Actual vs Predicted points)
best_predictions = best_model.predict(X_test)
evaluation_data = {
    "actual": [float(val) for val in y_test],
    "predicted": [float(val) for val in best_predictions]
}
evaluation_path = os.path.join(ml_dir, "evaluation_data.pkl")
joblib.dump(evaluation_data, evaluation_path)
print(f"Evaluation data saved to:\n{evaluation_path}")

print("\nModel training with preprocessing & cross-validation completed successfully!")