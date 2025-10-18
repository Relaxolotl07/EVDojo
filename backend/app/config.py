from dataclasses import dataclass, field
from typing import List, Set, Dict
import os


@dataclass
class Config:
    max_variants: int = 3
    allowed_reason_tags: List[str] = field(
        default_factory=lambda: [
            "clearer_ask",
            "fewer_hedges",
            "more_specific",
            "concise",
            "tone_polite",
            "structure",
        ]
    )
    # Judge orchestration threshold
    rm_accept_margin: float = 0.4
    # Rater skill initialization
    expert_alpha: float = 1.5
    crowd_alpha: float = 1.0
    llm_alpha: float = 1.0
    # Safety
    blocked_goal_keywords: Set[str] = field(
        default_factory=lambda: {"harassment", "deception", "impersonation", "harm"}
    )

    # Streaming mode flags and thresholds
    streaming_enabled: bool = field(default_factory=lambda: os.getenv("STREAMING_ENABLED", "true").lower() == "true")
    streaming: Dict[str, float | int | Dict[str, int] | bool] = field(
        default_factory=lambda: {
            "tau_pos": 0.80,
            "tau_neg": 0.20,
            "min_persistence": 2,
            "cooldown_ms": {"light": 6000, "standard": 8000, "intense": 3000},
            "debounce_ms": 450,
            "require_agreement": True,
            "hi_conf_margin": 0.15,
        }
    )

    # Default RM version
    rm_version: str = "v1"

    # Debug/demo controls
    debug_demo: bool = field(default_factory=lambda: os.getenv("DEBUG_DEMO", "false").lower() in ("1", "true", "yes", "on"))
    # accept both DEBUG_DEMO_FORCE_EMIT and DEBUG_DEMO_FORCE_FIX_EMIT for convenience
    debug_demo_force_emit: bool = field(
        default_factory=lambda: (
            os.getenv("DEBUG_DEMO_FORCE_EMIT", "true").lower() in ("1", "true", "yes", "on")
            or os.getenv("DEBUG_DEMO_FORCE_FIX_EMIT", "").lower() in ("1", "true", "yes", "on")
        )
    )
    debug_fixed_goal: str = "debug: ask clearly and respectfully"
    debug_yes_word: str = "yes"
    debug_no_word: str = "no"

    # Predefined topics
    topics: List[str] = field(
        default_factory=lambda: [
            "internal-request",
            "customer-support",
            "networking",
            "ask-out",
        ]
    )

    # CORS / deployment
    cors_allow_origins_env: str = field(default_factory=lambda: os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,https://evdojo.com,https://www.evdojo.com,https://app.evdojo.com"))
    @property
    def cors_allow_origins(self) -> List[str]:
        return [o.strip() for o in self.cors_allow_origins_env.split(",") if o.strip()]


config = Config()
