"""
Document assistant grounded in MGC's three source documents.
Uses an LLM for natural-language understanding and response generation.
All arithmetic is delegated to calculator.py — never to the LLM.
"""

import json
import os
from pathlib import Path
from openai import OpenAI
from calculator import calculate_unit_price, format_pkr, UNIT_TYPES

DOCS_DIR = Path(__file__).parent / "docs"

TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "calculate_unit_price",
            "description": (
                "Calculate the exact total price for an MGC Aurora Heights unit. "
                "Call this for ANY question involving prices, costs, amounts, or payment breakdowns. "
                "NEVER do arithmetic yourself — always call this tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "unit_type": {
                        "type": "string",
                        "enum": UNIT_TYPES,
                        "description": "The unit type exactly as listed in the price sheet.",
                    },
                    "block": {
                        "type": "string",
                        "enum": ["A", "B"],
                    },
                    "floor": {
                        "type": "integer",
                        "description": "Floor number (1-22). Needed only when the question mentions a specific floor.",
                    },
                    "is_corner": {
                        "type": "boolean",
                        "description": "True if the question mentions a corner unit.",
                        "default": False,
                    },
                    "is_margalla_facing": {
                        "type": "boolean",
                        "description": "True if the question mentions Margalla-facing orientation.",
                        "default": False,
                    },
                    "payment_type": {
                        "type": "string",
                        "enum": ["standard", "full_cash", "50_percent_upfront"],
                        "description": "Payment approach. Use '50_percent_upfront' if buyer pays 50% upfront.",
                        "default": "standard",
                    },
                    "is_overseas": {
                        "type": "boolean",
                        "description": "True if the buyer is an overseas Pakistani.",
                        "default": False,
                    },
                    "is_second_unit": {
                        "type": "boolean",
                        "description": "True if this is the buyer's second unit.",
                        "default": False,
                    },
                },
                "required": ["unit_type", "block"],
            },
        },
    }
]


def _load_documents() -> str:
    """Load all three MGC documents into a single context string."""
    parts = []
    for md_file in sorted(DOCS_DIR.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        parts.append(f"=== DOCUMENT: {md_file.name} ===\n{text}")
    return "\n\n".join(parts)


SYSTEM_PROMPT = f"""You are an internal sales assistant for MGC Developments. You answer questions
using ONLY the three source documents provided below. Follow these rules strictly:

1. CITATION IS MANDATORY. Every factual claim must end with its source in this format:
   [Source: <filename> § <section heading>]
   An answer without a source is a wrong answer.

2. ARITHMETIC — NEVER compute prices, totals, percentages, or payment amounts yourself.
   Call the calculate_unit_price tool for ANY price-related question. Report exactly
   the numbers the tool returns.

3. CONFLICTING INFORMATION — If two documents state different values for the same fact,
   report BOTH values with their respective sources and flag the conflict. Do NOT pick one.

4. INFORMATION NOT IN DOCUMENTS — If the documents do not contain the answer, say so
   plainly: "This information is not available in the current documents." NEVER invent,
   estimate, or extrapolate.

5. EXPLICITLY UNCONFIRMED INFORMATION — If a document says something is unconfirmed,
   pending, or not yet decided, relay that status. Do not treat "discussions are ongoing"
   as a confirmed fact.

6. Keep answers concise and directly useful to a salesperson on a call.

--- SOURCE DOCUMENTS ---

{_load_documents()}

--- END OF DOCUMENTS ---"""


class DocumentAssistant:
    def __init__(self):
        api_key = os.environ.get("LLM_API_KEY", "")
        base_url = os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1")
        self.model = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def ask(self, question: str) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TOOL_SCHEMA,
            tool_choice="auto",
            temperature=0.1,
        )

        msg = response.choices[0].message

        # Handle tool calls (calculator)
        if msg.tool_calls:
            messages.append(msg)
            for tool_call in msg.tool_calls:
                args = json.loads(tool_call.function.arguments)
                result = calculate_unit_price(**args)
                if "error" not in result:
                    readable = _format_calculation(result)
                else:
                    readable = result["error"]
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": readable,
                })

            followup = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
            )
            return followup.choices[0].message.content

        return msg.content


def _format_calculation(calc: dict) -> str:
    """Turn calculator output into a readable string the LLM can cite."""
    lines = [
        f"Unit: {calc['unit_type']}, Block {calc['block']} ({calc['covered_area_sqft']} sq ft)",
        f"Base price: PKR {format_pkr(calc['base_price'])}",
    ]
    if calc["premiums"]:
        for p in calc["premiums"]:
            lines.append(f"  + {p['label']}: +{p['rate']:.0%} = PKR {format_pkr(p['amount'])}")
        lines.append(f"Total premium: +{calc['total_premium_rate']:.0%} = PKR {format_pkr(calc['total_premium_amount'])}")
    if calc["discounts"]:
        for d in calc["discounts"]:
            lines.append(f"  − {d['label']}: −{d['rate']:.0%}")
        lines.append(f"Total discount on base: −{calc['total_discount_rate']:.0%} = PKR {format_pkr(calc['total_discount_amount'])}")
        lines.append(f"Discounted base: PKR {format_pkr(calc['discounted_base'])}")
    lines.append(f"TOTAL UNIT PRICE: PKR {format_pkr(calc['total_unit_price'])}")
    lines.append("")
    plan = calc["payment_plan"]
    lines.append(f"Payment plan breakdown:")
    lines.append(f"  Booking (10%):       PKR {format_pkr(plan['booking_10pct'])}")
    lines.append(f"  Confirmation (10%):  PKR {format_pkr(plan['confirmation_10pct'])}")
    lines.append(f"  Each quarterly (3.75%): PKR {format_pkr(plan['quarterly_instalment_each_3_75pct'])} × 16")
    lines.append(f"  Quarterly total (60%):  PKR {format_pkr(plan['quarterly_instalments_total_60pct'])}")
    lines.append(f"  Possession (20%):    PKR {format_pkr(plan['possession_20pct'])}")
    lines.append("")
    lines.append(f"Sources: {', '.join(calc['sources'])}")
    return "\n".join(lines)
