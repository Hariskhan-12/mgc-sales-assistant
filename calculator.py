"""
Programmatic price calculator for MGC Aurora Heights.
All arithmetic happens here — never in the LLM.
"""

BASE_PRICES = {
    ("Studio", "A"):          {"sqft": 480,  "price": 8_640_000},
    ("1-Bed Standard", "A"):  {"sqft": 720,  "price": 13_320_000},
    ("2-Bed Standard", "A"):  {"sqft": 1150, "price": 21_850_000},
    ("1-Bed Standard", "B"):  {"sqft": 720,  "price": 13_680_000},
    ("2-Bed Standard", "B"):  {"sqft": 1150, "price": 22_425_000},
    ("2-Bed Corner", "B"):    {"sqft": 1310, "price": 26_855_000},
    ("3-Bed Executive", "B"): {"sqft": 1880, "price": 39_480_000},
    ("4-Bed Penthouse", "B"): {"sqft": 3400, "price": 88_400_000},
}

UNIT_TYPES = list({k[0] for k in BASE_PRICES})


def calculate_unit_price(
    unit_type: str,
    block: str,
    floor: int | None = None,
    is_corner: bool = False,
    is_margalla_facing: bool = False,
    payment_type: str = "standard",
    is_overseas: bool = False,
    is_second_unit: bool = False,
) -> dict:
    key = (unit_type, block.upper())
    if key not in BASE_PRICES:
        return {"error": f"{unit_type} is not available in Block {block.upper()}. "
                         f"Check 02_price_list_payment_plan.md — Base Prices."}

    info = BASE_PRICES[key]
    base = info["price"]
    sqft = info["sqft"]
    sources = []
    premiums = []
    premium_rate = 0.0

    sources.append(f"02_price_list_payment_plan.md § Base Prices (Block {block.upper()})")

    # --- location premiums (cumulative, on base price) ---
    if floor is not None:
        if 13 <= floor <= 19:
            premium_rate += 0.04
            premiums.append({"label": f"Floor {floor} (floors 13–19)", "rate": 0.04, "amount": round(base * 0.04)})
        elif 20 <= floor <= 22:
            premium_rate += 0.07
            premiums.append({"label": f"Floor {floor} (floors 20–22)", "rate": 0.07, "amount": round(base * 0.07)})

    if is_corner:
        premium_rate += 0.03
        premiums.append({"label": "Corner unit", "rate": 0.03, "amount": round(base * 0.03)})

    if is_margalla_facing:
        premium_rate += 0.06
        premiums.append({"label": "Margalla-facing", "rate": 0.06, "amount": round(base * 0.06)})

    if premiums:
        sources.append("02_price_list_payment_plan.md § Location Premiums")

    premium_amount = round(base * premium_rate)

    # --- discounts (on base price only; premiums are NOT discounted) ---
    discount_rate = 0.0
    discounts = []

    if payment_type == "full_cash":
        discount_rate += 0.12
        discounts.append({"label": "Full cash payment", "rate": 0.12})
    elif payment_type == "50_percent_upfront":
        discount_rate += 0.06
        discounts.append({"label": "50% upfront", "rate": 0.06})

    if is_overseas:
        discount_rate += 0.02
        discounts.append({"label": "Overseas Pakistani (RDA)", "rate": 0.02})

    if is_second_unit:
        discount_rate += 0.015
        discounts.append({"label": "Second unit by same buyer", "rate": 0.015})

    if discounts:
        sources.append("02_price_list_payment_plan.md § Discounts")

    discount_amount = round(base * discount_rate)
    discounted_base = base - discount_amount
    total_unit_price = discounted_base + premium_amount

    # --- payment plan ---
    plan = {
        "booking_10pct":       round(total_unit_price * 0.10),
        "confirmation_10pct":  round(total_unit_price * 0.10),
        "quarterly_instalment_each_3_75pct": round(total_unit_price * 0.0375),
        "quarterly_instalments_total_60pct": round(total_unit_price * 0.60),
        "possession_20pct":    round(total_unit_price * 0.20),
    }
    sources.append("02_price_list_payment_plan.md § Standard Payment Plan (4 years)")

    # --- other charges ---
    maintenance_advance = round(12 * 9.50 * sqft)
    other_charges = {
        "utility_connection": 285_000,
        "parking_mandatory":  1_450_000,
        "maintenance_advance_12mo": maintenance_advance,
    }
    sources.append("02_price_list_payment_plan.md § Other Charges")

    return {
        "unit_type": unit_type,
        "block": block.upper(),
        "covered_area_sqft": sqft,
        "base_price": base,
        "premiums": premiums,
        "total_premium_rate": premium_rate,
        "total_premium_amount": premium_amount,
        "discounts": discounts,
        "total_discount_rate": discount_rate,
        "total_discount_amount": discount_amount,
        "discounted_base": discounted_base,
        "total_unit_price": total_unit_price,
        "payment_plan": plan,
        "other_charges": other_charges,
        "sources": sources,
    }


def format_pkr(amount: int) -> str:
    """Format amount in Pakistani convention: 1,23,45,678"""
    s = str(amount)
    if len(s) <= 3:
        return s
    result = s[-3:]
    s = s[:-3]
    while s:
        result = s[-2:] + "," + result
        s = s[:-2]
    return result
