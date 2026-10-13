# MGC Sales Assistant

A document Q&A assistant and lead scoring system for MGC Aurora Heights. A salesperson can ask questions about pricing, payment plans, and booking policy — grounded in source documents with citations — and score incoming leads by conversion likelihood.

---

## Quick Start

```bash
pip install -r requirements.txt
python ml_model.py          # train the lead scoring model (~5 seconds)
python app.py               # start web server at http://localhost:8000
```

### LLM Setup (for Part 1 — Document Assistant)

The document assistant needs an LLM API. **Groq is free:**

1. Go to [console.groq.com/keys](https://console.groq.com/keys) and sign up (Google/GitHub, 30 seconds)
2. Create an API key
3. Copy `.env.example` to `.env` and paste your key:

```bash
cp .env.example .env
# edit .env and set LLM_API_KEY=gsk_your_key_here
```

The lead scoring (Part 3) and SQL (Part 2) work without any API key.

---

## Project Structure

```
app.py                  FastAPI backend — serves API + frontend (Part 4)
assistant.py            Document assistant — LLM + function calling (Part 1)
calculator.py           Programmatic price calculator — all math here (Part 1)
ml_model.py             Lead scoring — training + prediction (Part 3)
schema.sql              SQL schema for the leads CRM (Part 2)
queries.sql             Three SQL queries (Part 2)
frontend/               Next.js + React + TypeScript frontend (Part 4)
  src/app/page.tsx        Main page with tab navigation
  src/components/         ChatPanel, ScoringPanel, ScoreGauge
  src/lib/api.ts          Type-safe API client
  out/                    Pre-built static export (served by FastAPI)
docs/                   Source documents (given)
leads.csv               Leads dataset (given)
```

---

## Part 1 — Document Assistant

**Architecture:** All three documents (~2 KB each) are loaded directly into the LLM system prompt — no vector store needed. The LLM handles natural language understanding, citation, conflict detection, and refusal. All price arithmetic is delegated to a **Python calculator** via function calling; the LLM never computes numbers itself.

**Why this design:**
- Documents are small enough for full context (better than chunked retrieval)
- Function calling separates what LLMs are good at (language) from what they're bad at (arithmetic)
- The calculator returns exact numbers with source references, so the LLM cites correctly

**How hard cases are handled:**

| Question | Handling |
|----------|----------|
| Transfer fee | **Conflict detected.** Price list says 2%, booking FAQ says 2.5%. Both values reported with their sources; the conflict is explicitly flagged. |
| Rental yield | **Refusal.** Not in documents. The FAQ says "MGC does not publish rental yield projections." The system cites this and declines to guess. |
| Anchor tenant | **Unconfirmed.** Brochure says "no anchor tenant has been confirmed." System reports the status, not a fabricated answer. |
| Price calculations | **Programmatic.** `calculator.py` handles all arithmetic — base price lookup, cumulative premium stacking, discount application, payment plan breakdown. The LLM extracts parameters and reports the calculator's exact output. |

---

## Part 2 — Database

**`schema.sql`** — Single `leads` table. One table is defensible: every column describes a single lead record. Includes:
- Proper types and constraints
- `crm_record_hash BIGINT UNIQUE` — prevents duplicate inserts at the DB level
- Indexes on `source`, `city`, `created_at`, `converted`

**`queries.sql`** — Three queries, all validated against the actual data in SQLite:

1. **Conversion rate by source** (200+ leads, best first): Referral leads best at 13.2%, Expo Stall worst at 3.0%
2. **Duplicate detection**: Finds 160 duplicate pairs by `crm_record_hash`. Deterministic winner rule: keep the row whose `lead_id` sorts first alphabetically (original `MGC-XXXXX` beats the duplicate `MGC-XXXXX-B`). Schema-level fix: `UNIQUE` constraint on `crm_record_hash`.
3. **City normalization**: In-query `CASE WHEN` maps ISB/ISLAMABAD → Islamabad, Rwp/RAWALPINDI → Rawalpindi, khi/KARACHI → Karachi, etc.

---

## Part 3 — ML Lead Scoring

### Data cleaning decisions

| Decision | Reason |
|----------|--------|
| **Dropped `token_amount_received_pkr`** | Direct leakage — token receipt is part of the conversion process itself |
| **Dropped `calls_made`, `total_call_seconds`, `whatsapp_replies`, `site_visits`** | Temporal leakage — these accumulate over the lead's lifecycle. At intake time (when we'd score a new lead), we don't have these values. |
| **Dropped `lead_id`, `crm_record_hash`** | Identifiers, not predictive features |
| **Kept `has_financing_approved`** | Borderline — could be pre-approved before engagement (valid) or approved during sales (leakage). Erred on inclusion; noted in this README. |
| **Kept `agent_experience_years`** | About the assigned agent, not the lead. Could be confounded (experienced agents get better leads), but included as a legitimate signal. |
| **Normalized cities** | ISB → Islamabad, Rwp → Rawalpindi, khi → Karachi, etc. |
| **Removed 160 duplicates** | Kept original entry, dropped `-B` suffix rows |
| **Imputed missing values** | Median for numeric, "Unknown" for categorical |

### Time-based split

- **Train:** 7,200 leads (Jan 2024 – May 2025)
- **Test:** 1,800 leads (May 2025 – Oct 2025)

**Why this matters:** In production, we score *new* leads using only *past* data. A random split would let the model see future patterns during training, inflating metrics. A time split simulates real deployment: train on history, evaluate on the future.

### Model and metric

- **Model:** Logistic Regression (scikit-learn, no tuning — honest baseline)
- **AUC-ROC:** 0.759

**Business metric:** If the sales team can only call the **top 100 model-scored leads**:
- **Model: 34 convert** out of 100
- **Random: ~8 convert** out of 100 (no-skill baseline at 7.9% conversion rate)
- **4.3x lift** — the model is 4.3 times better than calling leads in random order

---

## Part 4 — Web Interface

Single-page app with two tabs:

1. **Document Assistant** — Chat interface with conversation history. Type a question, get a grounded answer with source citations. Includes example questions for the six test cases.
2. **Lead Scoring** — Form to enter lead details. Returns conversion probability with a visual gauge and priority level (HIGH / MEDIUM / LOW).

**Stack:** FastAPI backend + Next.js 14 / React / TypeScript / Tailwind CSS frontend. The frontend is pre-built as a static export (`frontend/out/`) and served directly by FastAPI — no Node.js required to run.

**Frontend rebuild** (only needed if you modify the React components):
```bash
cd frontend && npm install && npm run build
```

---

## What's unfinished / what I'd do with more time

- **Model improvements:** Try gradient boosting (LightGBM/XGBoost) for better AUC; add feature importance to scoring response
- **Confidence calibration:** Logistic regression probabilities can be poorly calibrated — would add Platt scaling
- **Calculator API:** Expose `calculator.py` as a direct API endpoint, not just via LLM tool calls
- **Conversation memory:** Let the assistant reference earlier questions in the same session
- **SQL validation step:** Auto-run `schema.sql` + `queries.sql` against SQLite as a CI check

---

## Short-Answer Responses

**1. How does your system handle a question the documents don't answer?**
The system prompt instructs the LLM to say "This information is not available in the current documents" and never fabricate. For explicitly unconfirmed facts (like the anchor tenant), it reports the status from the document. For rental yield, it cites the FAQ's instruction that MGC doesn't publish projections and directs to the marketing manager.

**2. What did you clean, change, or drop in the leads data, and why?**
Dropped five columns as temporal leakage (`token_amount_received_pkr`, `calls_made`, `total_call_seconds`, `whatsapp_replies`, `site_visits`) — they accumulate during the sales process and wouldn't be known at intake time. Removed 160 duplicate rows by `crm_record_hash`. Normalized city names (ISB/Rwp/khi → proper names). Imputed missing values with median (numeric) and "Unknown" (categorical).

**3. Which metric did you use to judge your model, and why that one?**
"Top-100 conversions" — if the team calls only the 100 highest-scored leads, how many convert? This directly mirrors the business constraint (limited calling capacity) and is more actionable than AUC alone. The model gets 34 out of 100 vs ~8 from random, a 4.3x lift.

**4. What's unfinished, and what would you do with more time?**
Would try gradient boosting for better AUC, add confidence calibration, expose the calculator as a standalone API, and add feature importance explanations to the scoring output. Would also add conversation memory to the assistant and run the SQL queries as automated validation.

**5. Which AI tools did you use, and where did they help or get in the way?**
Used Claude Code for scaffolding, code generation, and iterative testing. It was strongest at boilerplate (FastAPI routes, HTML structure, sklearn pipeline) and weakest at getting arithmetic right in natural language — which is exactly why the calculator exists as a separate Python module. The architecture decision (LLM for language, Python for math) came from knowing this limitation.
