CREATE TABLE leads (
    lead_id              VARCHAR(20)   PRIMARY KEY,
    created_at           TIMESTAMP     NOT NULL,
    source               VARCHAR(50)   NOT NULL,
    city                 VARCHAR(50),
    area                 VARCHAR(100),
    property_type        VARCHAR(50),
    budget_pkr_lac       DECIMAL(10,2),
    bedrooms             SMALLINT,
    first_response_min   DECIMAL(10,2),
    calls_made           INT           DEFAULT 0,
    total_call_seconds   DECIMAL(10,2) DEFAULT 0,
    whatsapp_replies     INT           DEFAULT 0,
    site_visits          INT           DEFAULT 0,
    agent_experience_yrs DECIMAL(4,2),
    is_overseas          BOOLEAN       DEFAULT FALSE,
    referred_by_client   BOOLEAN       DEFAULT FALSE,
    has_financing        BOOLEAN       DEFAULT FALSE,
    token_amount_pkr     DECIMAL(15,2) DEFAULT 0,
    converted            BOOLEAN       DEFAULT FALSE,

    -- dedup: hash of identity fields (name/phone/email), reject duplicate inserts
    crm_record_hash      BIGINT        UNIQUE NOT NULL
);

CREATE INDEX idx_leads_source     ON leads(source);
CREATE INDEX idx_leads_city       ON leads(city);
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE INDEX idx_leads_converted  ON leads(converted);
