import os
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.kb import KnowledgeBase

CONFIDENCE_THRESHOLD = float(os.environ.get("CONF_THRESHOLD", "0.5"))


class Ticket(BaseModel):
    text: str = Field(min_length=3, max_length=2000, description="The ticket text")


def create_app(model_dir=None, kb_dir=None):
    model_dir = Path(model_dir or os.environ.get("MODEL_DIR", "models"))
    kb_dir = Path(kb_dir or os.environ.get("KB_DIR", "kb"))
    state = {}

    @asynccontextmanager
    async def lifespan(_app):
        state["model"] = joblib.load(model_dir / "model.joblib")
        state["kb"] = KnowledgeBase(kb_dir)
        yield
        state.clear()

    app = FastAPI(title="Ticket Triage", version="1.0.0", lifespan=lifespan)

    def predict(text):
        model = state["model"]
        probabilities = model.predict_proba([text])[0]
        ranked = sorted(zip(model.classes_, probabilities), key=lambda pair: pair[1], reverse=True)
        best_label, best_score = ranked[0]
        return {
            "category": str(best_label),
            "confidence": round(float(best_score), 3),
            "low_confidence": bool(best_score < CONFIDENCE_THRESHOLD),
            "scores": {str(label): round(float(p), 3) for label, p in ranked[:3]},
        }

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "categories": [str(c) for c in state["model"].classes_],
            "kb_articles": len(state["kb"]),
        }

    @app.post("/classify")
    def classify(ticket: Ticket):
        return predict(ticket.text)

    @app.post("/suggest")
    def suggest(ticket: Ticket):
        result = predict(ticket.text)
        result["articles"] = state["kb"].search(ticket.text)
        return result

    return app


app = create_app()
