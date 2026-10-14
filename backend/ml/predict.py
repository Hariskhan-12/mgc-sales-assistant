import pickle
import numpy as np
import pandas as pd

from .config import MODEL_PATH, FEATURE_COLS_PATH, NUMERIC, CATEGORICAL
from .preprocessing import normalize_city


def load_model():
    with open(MODEL_PATH, "rb") as f:
        pipeline = pickle.load(f)
    with open(FEATURE_COLS_PATH, "rb") as f:
        features = pickle.load(f)
    return pipeline, features


def score_lead(lead_data: dict) -> float:
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
