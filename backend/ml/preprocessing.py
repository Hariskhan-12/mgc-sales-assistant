import pandas as pd
from .config import TIME_COL, BINARY, TARGET, CITY_MAP


def normalize_city(city) -> str:
    if pd.isna(city) or str(city).strip() == "":
        return "Unknown"
    return CITY_MAP.get(str(city).strip().lower(), str(city).strip().title())


def load_and_clean(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df[TIME_COL] = pd.to_datetime(df[TIME_COL])

    df = df.sort_values("lead_id").drop_duplicates(subset="crm_record_hash", keep="first")

    df["city_clean"] = df["city"].apply(normalize_city)
    df["area"] = df["area"].fillna("Unknown")

    for col in BINARY:
        df[col] = df[col].astype(int)
    df[TARGET] = df[TARGET].astype(int)

    return df
