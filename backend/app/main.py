from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.proxy_headers import ProxyHeadersMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import items, variants, rank, compare, duel, rm, judge, expert, moderate, abuse, metrics, debug, topics, import_emails, expert_pairs, users, health
from .config import config
from .middleware import RequestIDMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title="Comparative Coaching Platform (MVP)")
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(items.router)
    app.include_router(variants.router)
    app.include_router(rank.router)
    app.include_router(compare.router)
    app.include_router(duel.router)
    app.include_router(rm.router)
    app.include_router(judge.router)
    app.include_router(expert.router)
    app.include_router(expert_pairs.router)
    app.include_router(moderate.router)
    app.include_router(abuse.router)
    app.include_router(metrics.router)
    app.include_router(topics.router)
    app.include_router(import_emails.router)
    app.include_router(users.router)
    app.include_router(health.router)
    app.include_router(debug.router)
    # Serve local frontend for quick testing
    try:
        app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
    except Exception:
        # If frontend dir missing, skip mounting
        pass
    return app


app = create_app()
