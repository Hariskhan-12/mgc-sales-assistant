from .calculator import UNIT_TYPES, format_pkr

TOOL_SCHEMA_BEDROCK = [
    {
        "toolSpec": {
            "name": "calculate_unit_price",
            "description": (
                "Calculate the exact total price for an MGC Aurora Heights unit. "
                "Call this for ANY question involving prices, costs, amounts, or payment breakdowns. "
                "NEVER do arithmetic yourself."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "unit_type": {
                            "type": "string",
                            "enum": UNIT_TYPES,
                            "description": "Unit type from the price sheet.",
                        },
                        "block": {
                            "type": "string",
                            "enum": ["A", "B"],
                        },
                        "floor": {
                            "type": "integer",
                            "description": "Floor number (1-22).",
                        },
                        "is_corner": {
                            "type": "boolean",
                            "description": "Corner unit.",
                        },
                        "is_margalla_facing": {
                            "type": "boolean",
                            "description": "Margalla-facing orientation.",
                        },
                        "payment_type": {
                            "type": "string",
                            "enum": ["standard", "full_cash", "50_percent_upfront"],
                            "description": "Payment approach.",
                        },
                        "is_overseas": {
                            "type": "boolean",
                            "description": "Overseas Pakistani buyer.",
                        },
                        "is_second_unit": {
                            "type": "boolean",
                            "description": "Second unit by same buyer.",
                        },
                    },
                    "required": ["unit_type", "block"],
                }
            },
        }
    }
]


def format_calculation(calc: dict) -> str:
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
            lines.append(f"  - {d['label']}: -{d['rate']:.0%}")
        lines.append(f"Total discount on base: -{calc['total_discount_rate']:.0%} = PKR {format_pkr(calc['total_discount_amount'])}")
        lines.append(f"Discounted base: PKR {format_pkr(calc['discounted_base'])}")
    lines.append(f"TOTAL UNIT PRICE: PKR {format_pkr(calc['total_unit_price'])}")
    lines.append("")
    plan = calc["payment_plan"]
    lines.append("Payment plan breakdown:")
    lines.append(f"  Booking (10%):       PKR {format_pkr(plan['booking_10pct'])}")
    lines.append(f"  Confirmation (10%):  PKR {format_pkr(plan['confirmation_10pct'])}")
    lines.append(f"  Each quarterly (3.75%): PKR {format_pkr(plan['quarterly_instalment_each_3_75pct'])} x 16")
    lines.append(f"  Quarterly total (60%):  PKR {format_pkr(plan['quarterly_instalments_total_60pct'])}")
    lines.append(f"  Possession (20%):    PKR {format_pkr(plan['possession_20pct'])}")
    lines.append("")
    lines.append(f"Sources: {', '.join(calc['sources'])}")
    return "\n".join(lines)
