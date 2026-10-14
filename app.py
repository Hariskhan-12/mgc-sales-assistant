import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
load_dotenv()

import gradio as gr
from assistant import DocumentAssistant
from ml import score_lead

assistant = None

def get_assistant():
    global assistant
    if assistant is None:
        assistant = DocumentAssistant()
    return assistant


def chat_fn(message, history):
    try:
        return get_assistant().ask(message)
    except Exception as e:
        return f"Error: {str(e)}"


def score_fn(source, city, area, property_type, budget, bedrooms,
             response_min, agent_exp, overseas, referred, financing):
    try:
        lead = {
            "source": source, "city": city, "area": area or "Unknown",
            "property_type": property_type,
            "budget_pkr_lac": float(budget) if budget else None,
            "bedrooms": int(bedrooms) if bedrooms else None,
            "first_response_minutes": float(response_min) if response_min else None,
            "agent_experience_years": float(agent_exp) if agent_exp else None,
            "is_overseas": 1 if overseas else 0,
            "referred_by_existing_client": 1 if referred else 0,
            "has_financing_approved": 1 if financing else 0,
        }
        prob = score_lead(lead)
        pct = round(prob * 100, 1)

        if pct >= 15:
            priority = "HIGH - Call immediately"
        elif pct >= 8:
            priority = "MEDIUM - Follow up within 24h"
        else:
            priority = "LOW - Add to nurture queue"

        return f"## {pct}% conversion probability\n### {priority}"
    except Exception as e:
        return f"Error: {str(e)}"


EXAMPLES = [
    "What is the base price of a 2-bed in Block B?",
    "What is the total for a Margalla-facing corner unit on floor 15, 2-bed Block B?",
    "An overseas Pakistani buyer pays 50% upfront on a 3-Bed Executive - what's the price and booking amount?",
    "What is the transfer fee?",
    "What is the rental yield on a 1-bed?",
    "Who is the anchor tenant?",
]

SOURCES = ["Facebook Ads", "Property Portal", "Google Search", "Instagram",
           "Referral", "Walk-in", "WhatsApp Campaign", "Expo Stall", "Billboard"]
CITIES = ["Islamabad", "Rawalpindi", "Lahore", "Karachi", "Peshawar",
          "Faisalabad", "Multan", "Gujranwala", "Abbottabad"]
PTYPES = ["Apartment", "Commercial Shop", "Penthouse", "Plot", "Farmhouse", "House"]

with gr.Blocks(title="MGC Sales Assistant", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# MGC Sales Assistant\nAurora Heights - GT Road, Islamabad")

    with gr.Tab("Document Assistant"):
        gr.Markdown("Ask about pricing, payment plans, and booking policy. Every answer cites its source.")
        chatbot = gr.ChatInterface(
            fn=chat_fn,
            examples=EXAMPLES,
            chatbot=gr.Chatbot(height=450),
        )

    with gr.Tab("Lead Scoring"):
        gr.Markdown("Enter lead details to predict conversion likelihood.")
        with gr.Row():
            source = gr.Dropdown(SOURCES, value="Facebook Ads", label="Lead Source")
            city = gr.Dropdown(CITIES, value="Islamabad", label="City")
            ptype = gr.Dropdown(PTYPES, value="Apartment", label="Property Type")
        with gr.Row():
            area = gr.Textbox(value="Bahria Town", label="Area / Society")
            budget = gr.Number(value=200, label="Budget (PKR Lac)")
            beds = gr.Number(value=2, label="Bedrooms", precision=0)
        with gr.Row():
            resp = gr.Number(value=15, label="First Response (min)")
            exp = gr.Number(value=3.0, label="Agent Experience (yrs)")
        with gr.Row():
            overseas = gr.Checkbox(label="Overseas Pakistani")
            referred = gr.Checkbox(label="Referred by client")
            fin = gr.Checkbox(label="Financing pre-approved")

        score_btn = gr.Button("Score This Lead", variant="primary")
        result = gr.Markdown()

        score_btn.click(
            fn=score_fn,
            inputs=[source, city, area, ptype, budget, beds, resp, exp, overseas, referred, fin],
            outputs=result,
        )

demo.launch(server_name="0.0.0.0", server_port=7860)
