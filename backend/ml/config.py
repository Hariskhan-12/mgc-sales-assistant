from pathlib import Path

MODEL_PATH = Path(__file__).parent / "lead_model.pkl"
FEATURE_COLS_PATH = Path(__file__).parent / "feature_cols.pkl"
DATA_DIR = Path(__file__).parent.parent.parent / "data"

TARGET = "converted"
TIME_COL = "created_at"

# These columns leak info from the sales process itself
LEAKAGE_COLS = [
    "token_amount_received_pkr",
    "calls_made",
    "total_call_seconds",
    "whatsapp_replies",
    "site_visits",
]

ID_COLS = ["lead_id", "crm_record_hash"]

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
