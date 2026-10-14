-- Q1: conversion rate by source (only sources with 200+ leads)

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


-- Q2: find duplicates (same crm_record_hash, different lead_id)
-- keep the one that sorts first alphabetically (original vs "-B" suffix)

SELECT
    a.lead_id   AS canonical_lead_id,
    b.lead_id   AS duplicate_lead_id,
    a.crm_record_hash
FROM leads a
JOIN leads b
    ON  a.crm_record_hash = b.crm_record_hash
    AND a.lead_id < b.lead_id;

-- delete the duplicates
DELETE FROM leads
WHERE lead_id IN (
    SELECT b.lead_id
    FROM leads a
    JOIN leads b
        ON  a.crm_record_hash = b.crm_record_hash
        AND a.lead_id < b.lead_id
);


-- Q3: conversion rate by city with inline normalization
-- handles inconsistent casing/abbreviations in the CRM

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
