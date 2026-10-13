"""
Lead scoring model — baseline logistic regression with time-based split.
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, precision_score

MODEL_PATH = Path(__file__).parent / "lead_model.pkl"
FEATURE_COLS_PATH = Path(__file__).parent / "feature_cols.pkl"

# --- Column classification ---
# LEAKAGE — these accumulate during the sales process and are unknown at intake
LEAKAGE_COLS = [
    "token_amount_received_pkr",  # part of conversion itself
    "calls_made",                 # accumulates over lead lifecycle
    "total_call_seconds",         # same
    "whatsapp_replies",           # same
    "site_visits",                # often happens as part of conversion funnel
]
ID_COLS = ["lead_id", "crm_record_hash"]
TARGET = "converted"
TIME_COL = "created_at"

CATEGORICAL = ["source", "city_clean", "area", "property_type"]
NUMERIC = ["budget_pkr_lac", "bedrooms", "first_response_minutes", "agent_experience_years"]
BINARY = ["is_overseas", "referred_by_existing_client", "has_financing_approved"]

CITY_MAP = {
    "islamabad": "Islamabad", "isb": "Islamabad",
    "rawalpindi": "Rawalpindi", "rwp": "Rawalpindi",
    "karachi": "Karachi", "khi": "Karachi",
    "lahore": "Lahore", "lhr": "Lahore",
    "peshawar": "Peshawar", "pew": "Peshawar",
    "faisalabad": "Faisalabad", "fsd": "Faisalabad",
    "multan": "Multan",
    "gujranwala": "Gujranwala",
    "abbottabad": "Abbottabad",
}


def normalize_city(city):
    if pd.isna(city) or str(city).strip() == "":
        return "Unknown"
    return CITY_MAP.get(str(city).strip().lower(), str(city).strip().title())


def load_and_clean(csv_path: str = "leads.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df[TIME_COL] = pd.to_datetime(df[TIME_COL])

    # Remove duplicates: keep the row whose lead_id sorts first (original entry)
    df = df.sort_values("lead_id").drop_duplicates(subset="crm_record_hash", keep="first")

    # Normalize city
    df["city_clean"] = df["city"].apply(normalize_city)

    # Fill missing area with "Unknown"
    df["area"] = df["area"].fillna("Unknown")

    # Binary cols: ensure int
    for col in BINARY:
        df[col] = df[col].astype(int)

    df[TARGET] = df[TARGET].astype(int)

    return df


def build_pipeline() -> Pipeline:
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])

    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    preprocessor = ColumnTransformer([
        ("num", numeric_pipe, NUMERIC),
        ("cat", categorical_pipe, CATEGORICAL),
        ("bin", "passthrough", BINARY),
    ])

    return Pipeline([
        ("preprocess", preprocessor),
        ("model", LogisticRegression(max_iter=1000, random_state=42)),
    ])


def train_and_evaluate(csv_path: str = "leads.csv"):
    df = load_and_clean(csv_path)
    df = df.sort_values(TIME_COL).reset_index(drop=True)

    # Time-based split: train on older 80%, test on newer 20%
    split_idx = int(len(df) * 0.8)
    train = df.iloc[:split_idx]
    test = df.iloc[split_idx:]

    features = CATEGORICAL + NUMERIC + BINARY
    X_train, y_train = train[features], train[TARGET]
    X_test, y_test = test[features], test[TARGET]

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    # Predictions
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    # --- Metrics ---
    auc = roc_auc_score(y_test, y_prob)

    # Business metric: top-100 leads — how many convert?
    test_with_scores = test.copy()
    test_with_scores["score"] = y_prob
    top_100 = test_with_scores.nlargest(100, "score")
    top_100_conversions = top_100[TARGET].sum()

    # No-skill baseline: random 100 picks
    conversion_rate = y_test.mean()
    random_100_expected = round(conversion_rate * 100, 1)

    print("=" * 60)
    print("LEAD SCORING MODEL — EVALUATION REPORT")
    print("=" * 60)
    print(f"Training set:  {len(train):,} leads  ({train[TIME_COL].min().date()} to {train[TIME_COL].max().date()})")
    print(f"Test set:      {len(test):,} leads  ({test[TIME_COL].min().date()} to {test[TIME_COL].max().date()})")
    print(f"Test conversion rate: {conversion_rate:.1%}")
    print()
    print(f"AUC-ROC: {auc:.3f}")
    print()
    print("BUSINESS METRIC — Top 100 scored leads:")
    print(f"  Model:      {top_100_conversions} out of 100 convert")
    print(f"  Random:     {random_100_expected} out of 100 would convert (no-skill baseline)")
    print(f"  Lift:       {top_100_conversions / max(random_100_expected, 0.1):.1f}x better than random")
    print()
    print("WHY TIME-BASED SPLIT MATTERS:")
    print("  In production, we predict conversion for NEW leads using only")
    print("  historical data. A random split leaks future patterns into training,")
    print("  giving unrealistically high scores. A time split mirrors real usage.")
    print()
    print("DROPPED COLUMNS (leakage risk):")
    for col in LEAKAGE_COLS:
        print(f"  - {col}")
    print("  These accumulate during the sales process. Using them would let the")
    print("  model 'see' information it wouldn't have when scoring a new lead.")
    print("=" * 60)

    # Save model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    with open(FEATURE_COLS_PATH, "wb") as f:
        pickle.dump(features, f)

    print(f"\nModel saved to {MODEL_PATH}")
    return pipeline, auc, top_100_conversions, random_100_expected


def load_model():
    with open(MODEL_PATH, "rb") as f:
        pipeline = pickle.load(f)
    with open(FEATURE_COLS_PATH, "rb") as f:
        features = pickle.load(f)
    return pipeline, features


def score_lead(lead_data: dict) -> float:
    """Score a single lead. Returns probability of conversion (0-1)."""
    pipeline, features = load_model()
    lead_data["city_clean"] = normalize_city(lead_data.get("city", ""))
    if "area" not in lead_data or not lead_data["area"]:
        lead_data["area"] = "Unknown"
    df = pd.DataFrame([lead_data])
    for col in features:
        if col not in df.columns:
            df[col] = np.nan if col in NUMERIC else "Unknown" if col in CATEGORICAL else 0
    prob = pipeline.predict_proba(df[features])[:, 1][0]
    return round(float(prob), 4)


if __name__ == "__main__":
    train_and_evaluate()
