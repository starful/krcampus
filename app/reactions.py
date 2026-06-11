# app/reactions.py
import os
from fastapi import APIRouter, Request, HTTPException
import firebase_admin
from firebase_admin import credentials, firestore
from starlette.concurrency import run_in_threadpool
from app.utils import get_client_ip

router = APIRouter()
COLLECTION_NAME = "jpcampus"

# ==========================================
# Firebase 초기화 세팅
# ==========================================
try:
    if not firebase_admin._apps:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app()
    db = firestore.client()
except Exception as e:
    print(f"🔥 Firebase initialization error: {e}")
    db = None

# ==========================================
# 좋아요/싫어요 API 엔드포인트
# ==========================================
@router.get("/reactions/{slug}")
async def get_reactions(slug: str):
    if db is None:
        return {"likes": 0, "dislikes": 0, "error": "Database not connected"}
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(slug)
        doc = await run_in_threadpool(doc_ref.get)
        if doc.exists:
            data = doc.to_dict()
            return {"likes": data.get("likes_count", 0), "dislikes": data.get("dislikes_count", 0)}
    except Exception as e:
        print(f"🔥 Read Error (DB not ready?): {e}")
    return {"likes": 0, "dislikes": 0}

def sync_process_reaction(db_client, collection_name, slug, safe_ip, new_type):
    post_ref = db_client.collection(collection_name).document(slug)
    reaction_ref = post_ref.collection('reactions').document(safe_ip)

    reaction_doc = reaction_ref.get()
    likes_inc, dislikes_inc = 0, 0
    batch = db_client.batch()

    if not reaction_doc.exists:
        if new_type == "like": likes_inc = 1
        else: dislikes_inc = 1
        batch.set(reaction_ref, {"type": new_type})
        current_type = None
    else:
        current_type = reaction_doc.to_dict().get("type")
        if current_type == new_type:
            if new_type == "like": likes_inc = -1
            else: dislikes_inc = -1
            batch.delete(reaction_ref)
        else:
            if new_type == "like":
                likes_inc = 1
                dislikes_inc = -1
            else:
                likes_inc = -1
                dislikes_inc = 1
            batch.update(reaction_ref, {"type": new_type})

    batch.set(post_ref, {
        "likes_count": firestore.Increment(likes_inc),
        "dislikes_count": firestore.Increment(dislikes_inc)
    }, merge=True)
    
    batch.commit()
    action_result = "added" if (not reaction_doc.exists) or current_type != new_type else "removed"
    
    updated_doc = post_ref.get()
    return action_result, updated_doc.to_dict() or {}

async def process_reaction(request: Request, slug: str, reaction_type: str):
    if db is None: raise HTTPException(status_code=500, detail="Database connection failed")

    safe_ip = get_client_ip(request).replace(".", "_").replace(":", "_")

    try:
        result, data = await run_in_threadpool(sync_process_reaction, db, COLLECTION_NAME, slug, safe_ip, reaction_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Reaction processing failed")

    return {
        "status": "success", "action": result,
        "likes": data.get("likes_count", 0), "dislikes": data.get("dislikes_count", 0),
        "current_type": reaction_type if result == "added" else None
    }

@router.post("/like/{slug}")
async def like_post(request: Request, slug: str): return await process_reaction(request, slug, "like")

@router.post("/dislike/{slug}")
async def dislike_post(request: Request, slug: str): return await process_reaction(request, slug, "dislike")