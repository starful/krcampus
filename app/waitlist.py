"""Checklist launch waitlist — same Firestore as reactions (REACTIONS_COLLECTION)."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from firebase_admin import firestore
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.http_utils import get_client_ip
from app.reactions import COLLECTION_NAME, db

router = APIRouter()

WAITLIST_DOC = "checklist_waitlist"
SIGNUPS = "signups"
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class WaitlistBody(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    lang: str = Field(default="en", max_length=8)
    source: str = Field(default="preview", max_length=64)
    website: str = Field(default="", max_length=200)  # honeypot


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _doc_id(email: str) -> str:
    return hashlib.sha256(email.encode("utf-8")).hexdigest()[:40]


def _sync_upsert(email: str, lang: str, source: str, ip: str) -> str:
    assert db is not None
    doc_id = _doc_id(email)
    ref = (
        db.collection(COLLECTION_NAME)
        .document(WAITLIST_DOC)
        .collection(SIGNUPS)
        .document(doc_id)
    )
    existing = ref.get()
    now = datetime.now(timezone.utc)
    if existing.exists:
        ref.set(
            {
                "email": email,
                "lang": lang,
                "source": source,
                "updated_at": now,
                "ip": ip,
            },
            merge=True,
        )
        return "exists"
    ref.set(
        {
            "email": email,
            "lang": lang,
            "source": source,
            "created_at": now,
            "updated_at": now,
            "ip": ip,
        }
    )
    parent = db.collection(COLLECTION_NAME).document(WAITLIST_DOC)
    parent.set(
        {
            "kind": "checklist_waitlist",
            "signups_count": firestore.Increment(1),
            "updated_at": now,
        },
        merge=True,
    )
    return "created"


@router.post("/checklist-waitlist")
async def checklist_waitlist(request: Request, body: WaitlistBody):
    if body.website.strip():
        # Bot honeypot — pretend success
        return {"status": "success", "action": "ignored"}

    email = _normalize_email(body.email)
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Invalid email")

    lang = (body.lang or "en").strip().lower()
    if lang not in {"en", "ja", "jp"}:
        lang = "en"
    if lang == "jp":
        lang = "ja"

    source = re.sub(r"[^a-zA-Z0-9_\-]", "", body.source or "preview")[:64] or "preview"

    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    ip = get_client_ip(request)
    try:
        action = await run_in_threadpool(_sync_upsert, email, lang, source, ip)
    except Exception as exc:
        print(f"🔥 Waitlist write error: {exc}")
        raise HTTPException(status_code=500, detail="Waitlist save failed") from exc

    return {"status": "success", "action": action}
