import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).parent
PROJECT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend" / "out"

load_dotenv(PROJECT_DIR / ".env")

sys.path.insert(0, str(BACKEND_DIR))
from assistant import DocumentAssistant
from ml import score_lead

app = FastAPI(title="MGC Sales Assistant")

_assistant = None


def get_assistant():
    global _assistant
    if _assistant is None:
        _assistant = DocumentAssistant()
    return _assistant


class QuestionRequest(BaseModel):
    question: str


class LeadRequest(BaseModel):
    source: str = ""
    city: str = ""
    area: str = ""
    property_type: str = ""
    budget_pkr_lac: float | None = None
    bedrooms: int | None = None
    first_response_minutes: float | None = None
    agent_experience_years: float | None = None
    is_overseas: int = 0
    referred_by_existing_client: int = 0
    has_financing_approved: int = 0


@app.post("/api/ask")
async def ask_question(req: QuestionRequest):
    try:
        answer = get_assistant().ask(req.question)
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"Error: {str(e)}\n\nMake sure LLM_API_KEY is set in your .env file."}


@app.post("/api/score")
async def score(req: LeadRequest):
    try:
        lead = req.model_dump()
        probability = score_lead(lead)
        pct = round(probability * 100, 1)

        if pct >= 15:
            priority = "HIGH - Call immediately"
        elif pct >= 8:
            priority = "MEDIUM - Follow up within 24h"
        else:
            priority = "LOW - Add to nurture queue"

        return {
            "score": probability,
            "percentage": pct,
            "priority": priority,
        }
    except Exception as e:
        return {"error": str(e)}


if FRONTEND_DIR.exists():
    app.mount("/_next", StaticFiles(directory=str(FRONTEND_DIR / "_next")), name="next-static")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
