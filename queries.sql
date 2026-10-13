-- ============================================================
-- Query 1: Conversion rate by lead source (200+ leads, best first)
-- ============================================================

SELECT
    source,
    COUNT(*)                                          AS total_leads,
    SUM(CASE WHEN converted THEN 1 ELSE 0 END)       AS conversions,
    ROUND(
        100.0 * SUM(CASE WHEN converted THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                 AS conversion_rate_pct
FROM leads
GROUP BY source
HAVING COUNT(*) >= 200
ORDER BY conversion_rate_pct DESC;


-- ============================================================
-- Query 2: Duplicate detection — keep one canonical row per pair
--
-- Duplicates share the same crm_record_hash (same person entered
-- by different agents). The "-B" suffix marks the later entry.
--
-- Deterministic winner rule: keep the row whose lead_id sorts first
-- alphabetically (i.e. "MGC-104183" beats "MGC-104183-B").
-- This always picks the original entry over the duplicate.
--
-- Schema-level prevention: a UNIQUE constraint on crm_record_hash
-- (see schema.sql) rejects the duplicate INSERT at the DB level.
-- ============================================================

-- Show the duplicate pairs:
SELECT
    a.lead_id   AS canonical_lead_id,
    b.lead_id   AS duplicate_lead_id,
    a.crm_record_hash
FROM leads a
JOIN leads b
    ON  a.crm_record_hash = b.crm_record_hash
    AND a.lead_id < b.lead_id;

-- Delete the non-canonical duplicates:
DELETE FROM leads
WHERE lead_id IN (
    SELECT b.lead_id
    FROM leads a
    JOIN leads b
        ON  a.crm_record_hash = b.crm_record_hash
        AND a.lead_id < b.lead_id
);


-- ============================================================
-- Query 3: Conversion rate by city, with in-query normalization
--
-- The CRM has inconsistent casing and abbreviations:
--   ISB / ISLAMABAD / Islamabad → Islamabad
--   Rwp / RAWALPINDI / Rawalpindi → Rawalpindi
--   khi / KARACHI / Karachi → Karachi
--   LAHORE / Lahore → Lahore  (etc.)
-- ============================================================

SELECT
    CASE
        WHEN UPPER(TRIM(city)) IN ('ISLAMABAD', 'ISB')             THEN 'Islamabad'
        WHEN UPPER(TRIM(city)) IN ('RAWALPINDI', 'RWP')            THEN 'Rawalpindi'
        WHEN UPPER(TRIM(city)) IN ('KARACHI', 'KHI')               THEN 'Karachi'
        WHEN UPPER(TRIM(city)) IN ('LAHORE', 'LHR')                THEN 'Lahore'
        WHEN UPPER(TRIM(city)) IN ('PESHAWAR', 'PEW')              THEN 'Peshawar'
        WHEN UPPER(TRIM(city)) IN ('FAISALABAD', 'FSD')            THEN 'Faisalabad'
        WHEN UPPER(TRIM(city)) IN ('MULTAN')                       THEN 'Multan'
        WHEN UPPER(TRIM(city)) IN ('GUJRANWALA')                   THEN 'Gujranwala'
        WHEN UPPER(TRIM(city)) IN ('ABBOTTABAD')                   THEN 'Abbottabad'
        ELSE INITCAP(TRIM(city))
    END                                                 AS city_normalized,
    COUNT(*)                                            AS total_leads,
    SUM(CASE WHEN converted THEN 1 ELSE 0 END)         AS conversions,
    ROUND(
        100.0 * SUM(CASE WHEN converted THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                   AS conversion_rate_pct
FROM leads
GROUP BY city_normalized
ORDER BY total_leads DESC;
