# MGC Sales Assistant

Internal tool for MGC Aurora Heights sales team. Two features:
1. **Document Q&A** — ask about pricing, payment plans, booking policy. Answers cite their source doc.
2. **Lead Scoring** — predict conversion probability for incoming leads.

## Setup

```bash
pip install -r backend/requirements.txt
python backend/train_model.py      # trains the scoring model (~5 sec)
python backend/app.py              # http://localhost:8000
```

You need a `.env` file in the project root for the document assistant to work:

```bash
cp .env.example .env
# fill in your LLM credentials
```

Lead scoring and SQL work without any API key.

## How it's organized

```
backend/
  app.py                    FastAPI server
  train_model.py            Run this to train the model
  assistant/                Document Q&A (Part 1)
    calculator.py             Price math — base prices, premiums, discounts, payment plans
    tools.py                  Function calling schema for the LLM
    document_loader.py        Loads the 3 source docs into the system prompt
    chat.py                   Sends questions to the LLM, handles tool calls
  ml/                       Lead scoring (Part 3)
    config.py                 Feature columns, city mappings
    preprocessing.py          Cleaning, dedup, city normalization
    pipeline.py               Sklearn pipeline (impute + scale + logistic regression)
    train.py                  Training with time-based split, prints metrics
    predict.py                Single-lead scoring for the API
frontend/                   Next.js 14 / React / TypeScript / Tailwind (Part 4)
  out/                      Pre-built static export, served by FastAPI
database/                   SQL (Part 2)
  schema.sql                CREATE TABLE with UNIQUE on crm_record_hash
  queries.sql               3 queries — conversion by source, dedup, city normalization
data/leads.csv              The dataset
docs/                       Source documents (brochure, price list, booking FAQ)
```

## Part 1 — Document Assistant

All 3 docs are small (~2KB each), so they go straight into the system prompt. No vector store, no chunking — just give the LLM the full context.

Price math is handled by `calculator.py` through function calling. The LLM figures out what the user is asking (unit type, block, floor, etc.), calls the calculator tool, and reports the exact numbers back. This way the LLM never does arithmetic.

Hard cases:
- **Transfer fee** — price list says 2%, booking FAQ says 2.5%. The system flags the conflict and says it'll check with a senior.
- **Rental yield** — not in the docs. System says so and doesn't guess.
- **Anchor tenant** — brochure says it's unconfirmed. System reports that status.

## Part 2 — Database

Single `leads` table — makes sense for this dataset since every column describes one lead. `crm_record_hash` has a UNIQUE constraint to prevent duplicate inserts.

Three queries in `queries.sql`:
1. Conversion rate by source (filtered to 200+ leads). Referrals convert best at 13.2%.
2. Duplicate detection via self-join on `crm_record_hash`. Finds 160 pairs. Keeps the original (alphabetically first `lead_id`), deletes the `-B` suffixed duplicate.
3. City normalization with CASE WHEN — maps ISB, Rwp, khi etc. to proper names.

## Part 3 — Lead Scoring

**Dropped columns:** `token_amount_received_pkr` (that's literally part of conversion), plus `calls_made`, `total_call_seconds`, `whatsapp_replies`, `site_visits` — these build up over the lead's lifecycle. At scoring time (when a new lead comes in) we don't have them.

Kept `has_financing_approved` even though it's borderline — could be pre-approved before we ever talk to them.

**Time-based split** — train on older 80%, test on newer 20%. A random split would let the model peek at future patterns which inflates the numbers. Time split reflects real usage: we always predict the future from the past.

**Results:**
- AUC: 0.759
- Top 100 model-scored leads: 34 convert (vs ~8 from random picks). That's a 4.3x lift.
- Logistic regression, no hyperparameter tuning. Simple baseline that actually works.

## Part 4 — Web Interface

Two tabs:
- Chat with the document assistant (example questions included)
- Score a lead through a form, get a probability + priority level

FastAPI serves the API endpoints and the pre-built Next.js frontend. No Node.js needed to run it.

To rebuild the frontend (only if you change React code):
```bash
cd frontend && npm install && npm run build
```

## What I'd do next

- Try LightGBM/XGBoost for better AUC
- Add feature importance to the scoring response
- Expose the calculator as its own API endpoint
- Add conversation memory to the assistant

## Short Answers

**1. How does your system handle questions the documents don't answer?**
It says "I don't have that information, let me check with my senior." For things explicitly unconfirmed (anchor tenant), it reports that status. For rental yield, it cites the FAQ saying MGC doesn't publish projections. It never makes things up.

**2. What did you clean/drop in the data, and why?**
Dropped 5 columns that leak sales-process data (token amount, call counts, whatsapp replies, site visits). Removed 160 duplicate rows by crm_record_hash. Normalized city names. Imputed missing values — median for numbers, "Unknown" for categories.

**3. Which metric and why?**
Top-100 conversions. If the sales team can only call 100 leads, how many convert? Model gets 34/100, random gets ~8/100. That's 4.3x better and directly maps to how the team would actually use this.

**4. What's unfinished?**
Would try gradient boosting for a better model, add calibration, expose the calculator as a standalone API, and add feature importance to explain why a lead scored high/low.

**5. Which AI tools did you use?**
Used GitHub Copilot for autocomplete and boilerplate. It's good for repetitive stuff (FastAPI routes, sklearn pipeline setup) but I wouldn't trust it with the business logic — the calculator and leakage detection I worked through myself.
