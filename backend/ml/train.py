import pickle
from sklearn.metrics import roc_auc_score

from .config import (
    MODEL_PATH, FEATURE_COLS_PATH, DATA_DIR,
    TARGET, TIME_COL, CATEGORICAL, NUMERIC, BINARY, LEAKAGE_COLS,
)
from .preprocessing import load_and_clean
from .pipeline import build_pipeline


def train_and_evaluate(csv_path: str = None):
    if csv_path is None:
        csv_path = str(DATA_DIR / "leads.csv")

    df = load_and_clean(csv_path)
    df = df.sort_values(TIME_COL).reset_index(drop=True)

    # 80/20 time-based split
    split_idx = int(len(df) * 0.8)
    train = df.iloc[:split_idx]
    test = df.iloc[split_idx:]

    features = CATEGORICAL + NUMERIC + BINARY
    X_train, y_train = train[features], train[TARGET]
    X_test, y_test = test[features], test[TARGET]

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_prob = pipeline.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_prob)

    test_with_scores = test.copy()
    test_with_scores["score"] = y_prob
    top_100 = test_with_scores.nlargest(100, "score")
    top_100_conversions = top_100[TARGET].sum()

    conversion_rate = y_test.mean()
    random_100 = round(conversion_rate * 100, 1)

    print(f"Train: {len(train):,} leads | Test: {len(test):,} leads")
    print(f"AUC-ROC: {auc:.3f}")
    print(f"Top 100: {top_100_conversions} conversions (vs {random_100} random baseline)")
    print(f"Lift: {top_100_conversions / max(random_100, 0.1):.1f}x")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    with open(FEATURE_COLS_PATH, "wb") as f:
        pickle.dump(features, f)

    print(f"Model saved to {MODEL_PATH}")
    return pipeline, auc, top_100_conversions, random_100
