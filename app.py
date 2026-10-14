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
            priority = "HIGH"
            color = "#059669"
            action = "Call immediately — strong buying signals."
        elif pct >= 8:
            priority = "MEDIUM"
            color = "#d97706"
            action = "Follow up within 24 hours."
        else:
            priority = "LOW"
            color = "#e11d48"
            action = "Add to nurture queue."

        return f"""
<div style="text-align:center; padding:30px;">
  <div style="font-size:56px; font-weight:800; color:{color};">{pct}%</div>
  <div style="font-size:14px; color:#64748b; margin-top:4px;">CONVERSION PROBABILITY</div>
  <div style="margin-top:16px;">
    <span style="background:{color}15; color:{color}; padding:8px 20px; border-radius:8px; font-weight:700; font-size:16px; border:1px solid {color}30;">{priority} PRIORITY</span>
  </div>
  <div style="margin-top:12px; color:#475569; font-size:14px;">{action}</div>
</div>
"""
    except Exception as e:
        return f"<div style='color:red; padding:20px;'>Error: {str(e)}</div>"


EXAMPLES = [
    ["What is the base price of a 2-bed in Block B?"],
    ["Total for a Margalla-facing corner unit on floor 15, 2-bed Block B?"],
    ["Overseas buyer pays 50% upfront on 3-Bed Executive — price and booking?"],
    ["What is the transfer fee?"],
    ["What is the rental yield on a 1-bed?"],
    ["Who is the anchor tenant?"],
]

SOURCES = ["Facebook Ads", "Property Portal", "Google Search", "Instagram",
           "Referral", "Walk-in", "WhatsApp Campaign", "Expo Stall", "Billboard"]
CITIES = ["Islamabad", "Rawalpindi", "Lahore", "Karachi", "Peshawar",
          "Faisalabad", "Multan", "Gujranwala", "Abbottabad"]
PTYPES = ["Apartment", "Commercial Shop", "Penthouse", "Plot", "Farmhouse", "House"]

CSS = """
.main-header { text-align: center; padding: 20px 0 10px; }
.main-header h1 { font-size: 28px; font-weight: 800; color: #1e293b; margin: 0; }
.main-header p { color: #64748b; font-size: 14px; margin-top: 4px; }
footer { display: none !important; }
"""

with gr.Blocks(title="MGC Sales Assistant", css=CSS, theme=gr.themes.Soft()) as demo:
    gr.HTML("""
    <div class="main-header">
        <h1>MGC Sales Assistant</h1>
        <p>Aurora Heights &bull; GT Road, Islamabad &bull; Internal Sales Tool</p>
    </div>
    """)

    with gr.Tab("Document Assistant"):
        gr.Markdown("Ask about pricing, payment plans, and booking policy. Answers are grounded in source documents with citations.")
        chatbot = gr.ChatInterface(
            fn=chat_fn,
            type="messages",
            examples=EXAMPLES,
            chatbot=gr.Chatbot(height=420, show_copy_button=True, type="messages"),
        )

    with gr.Tab("Lead Scoring"):
        gr.Markdown("Enter lead details to predict conversion likelihood using the trained ML model.")
        with gr.Row():
            with gr.Column(scale=2):
                with gr.Group():
                    gr.Markdown("### Lead Information")
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

                    score_btn = gr.Button("Score This Lead", variant="primary", size="lg")

            with gr.Column(scale=1):
                gr.Markdown("### Result")
                result = gr.HTML(value='<div style="text-align:center; padding:40px; color:#94a3b8;">Click "Score This Lead" to see the result</div>')

        score_btn.click(
            fn=score_fn,
            inputs=[source, city, area, ptype, budget, beds, resp, exp, overseas, referred, fin],
            outputs=result,
        )

demo.launch(server_name="0.0.0.0", server_port=7860)
