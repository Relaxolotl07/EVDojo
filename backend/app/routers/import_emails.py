from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import csv
from io import StringIO
from typing import List, Dict

from ..storage import db
from ..config import config
from ..variants import generate_text_variants


router = APIRouter(prefix="/import", tags=["import"])


@router.post("/emails")
async def import_emails(topic: str = Form(...), csv_file: UploadFile = File(...)):
    # Accept any topic string for dev; optionally append to known topics in-memory
    if topic not in config.topics:
        try:
            config.topics.append(topic)
        except Exception:
            pass
    content = await csv_file.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV too large (25MB max)")
    text = content.decode("utf-8", errors="ignore")
    reader = csv.DictReader(StringIO(text))
    required = ["email_id", "subject", "body"]
    for r in required:
        if r not in reader.fieldnames:
            raise HTTPException(status_code=400, detail=f"Missing column: {r}")

    count_items = 0
    count_pairs = 0
    for row in reader:
        email_id = row.get("email_id")
        subject = row.get("subject", "")
        body = row.get("body", "")
        context = {"goal": topic, "thread_id": row.get("thread_id"), "topic_hint": row.get("topic_hint")}
        # Create item with combined content; also keep subject/body in refs
        item_id = db.create_item(
            user_id="expert_import",
            modality="text",
            context=context,
            content_refs={"text": body, "subject": subject, "body": body},
            features={"length": len(body), "words": len(body.split())},
        )
        count_items += 1

        # generate variants (operate on body text, keep subject same)
        payload = {
            "modality": "text",
            "content_refs": {"text": body, "subject": subject, "body": body},
            "compact_features": {"length": len(body), "words": len(body.split())},
            "context": context,
        }
        variants = generate_text_variants(payload)
        created = []
        for v in variants[:2]:
            # force subject + body in variant content
            content_ref = {"subject": subject, "body": v["content_ref"].get("text")}
            vid = db.create_variant(item_id, content_ref, v["features"], v["diff_type"])
            created.append(vid)
        # Create pair with original baseline as A (store baseline as synthetic variant?)
        # Use first created variant against baseline: create baseline variant if not exists
        baseline_vid = db.create_variant(item_id, {"subject": subject, "body": body}, {"length": len(body), "words": len(body.split())}, "baseline")
        if created:
            db.create_pair(item_id=item_id, a_id=baseline_vid, b_id=created[0], topic=topic)
            count_pairs += 1

    return {"topic": topic, "import_id": db._next_id("import"), "count_items": count_items, "count_pairs": count_pairs}
