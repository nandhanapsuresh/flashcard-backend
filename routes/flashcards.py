from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db import sets_col
from nlp.generator import generate_flashcards
from bson import ObjectId
from datetime import datetime
import os
import random

router = APIRouter()
bearer = HTTPBearer()
SECRET = os.getenv("JWT_SECRET", "secret")

# ── Auth helper ──────────────────────────────────────────


def get_user_id(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        payload = jwt.decode(creds.credentials, SECRET, algorithms=["HS256"])
        return payload["sub"]
    except JWTError:
        raise HTTPException(401, "Invalid token")

# ── Generate flashcards ───────────────────────────────────


class NotesInput(BaseModel):
    title: str
    notes: str


@router.post("/generate")
def generate(data: NotesInput, user_id: str = Depends(get_user_id)):
    cards = generate_flashcards(data.notes)
    if not cards:
        raise HTTPException(
            400, "Could not generate flashcards from this text")

    set_doc = {
        "user_id": user_id,
        "title": data.title,
        "cards": cards,
        "created_at": datetime.utcnow().isoformat()
    }
    result = sets_col.insert_one(set_doc)
    return {"set_id": str(result.inserted_id), "card_count": len(cards)}

# ── Get all sets ──────────────────────────────────────────


@router.get("/sets")
def get_sets(user_id: str = Depends(get_user_id)):
    sets = list(sets_col.find({"user_id": user_id}))
    return [
        {
            "id": str(s["_id"]),
            "title": s["title"],
            "card_count": len(s["cards"]),
            "created_at": s["created_at"]
        }
        for s in sets
    ]

# ── Get cards for review (weighted) ──────────────────────


@router.get("/review/{set_id}")
def get_review(set_id: str, user_id: str = Depends(get_user_id)):
    s = sets_col.find_one({"_id": ObjectId(set_id), "user_id": user_id})
    if not s:
        raise HTTPException(404, "Set not found")

    cards = s["cards"]

    # Add index to each card for patching later
    for i, card in enumerate(cards):
        card["card_index"] = i

    known = [c for c in cards if c["status"] == "known"]
    not_known = [c for c in cards if c["status"] != "known"]

    # Show all cards once, but put not_known cards first
    # On subsequent reviews, not_known will dominate naturally
    review_order = not_known + known
    random.shuffle(not_known)
    random.shuffle(known)
    review_order = not_known + known

    return {"set_id": set_id, "cards": review_order}

# ── Mark card Known / Not Known ───────────────────────────


class StatusUpdate(BaseModel):
    card_index: int
    status: str


@router.patch("/card/{set_id}")
def update_card(
    set_id: str,
    data: StatusUpdate,
    user_id: str = Depends(get_user_id)
):
    s = sets_col.find_one({"_id": ObjectId(set_id), "user_id": user_id})
    if not s:
        raise HTTPException(404, "Set not found")

    cards = s["cards"]
    cards[data.card_index]["status"] = data.status
    cards[data.card_index]["review_count"] += 1

    sets_col.update_one(
        {"_id": ObjectId(set_id)},
        {"$set": {"cards": cards}}
    )
    return {"message": "Updated"}
