from fastapi import APIRouter, Request


router = APIRouter(prefix="", tags=["health"])


@router.get("/healthz")
def health(request: Request):
    return {
        "ok": True,
        "request_id": getattr(request.state, "request_id", None),
    }

