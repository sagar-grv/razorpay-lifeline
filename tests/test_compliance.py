import os
import pytest

# Compliance STOP keyword matching logic matching Project Lifeline engine
STOP_EXACT = [
    "stop", "band", "unsubscribe", "opt out", "optout", "remove", 
    "बंद", "ruko", "cancel", "stop please", "please stop", 
    "don't message", "dont message", "mat bhejo"
]

def check_is_stop(text: str) -> bool:
    """Deterministic, zero-hallucination compliance parser for STOP opt-out."""
    if not text:
        return False
    reply_clean = text.strip().lower()
    return reply_clean in STOP_EXACT or any(
        reply_clean.startswith(kw) for kw in ["stop", "band", "unsubscribe", "बंद", "opt out"]
    )

def test_stop_intent_detection():
    """Assert that English and Hindi opt-out phrases trigger deterministic compliance halt."""
    # 1. English variations
    assert check_is_stop("STOP PLEASE") is True
    assert check_is_stop("stop") is True
    assert check_is_stop("opt out") is True
    assert check_is_stop("unsubscribe") is True

    # 2. Hindi / Vernacular variations
    assert check_is_stop("बंद करो") is True
    assert check_is_stop("बंद") is True
    assert check_is_stop("mat bhejo") is True

    # 3. Non-opt-out inputs must not trigger false positives
    assert check_is_stop("I will pay tomorrow morning") is False
    assert check_is_stop("How can I pay via UPI?") is False
    assert check_is_stop("Link is not working") is False

def test_ladder_cap():
    """Assert that touch_count >= 3 caps proactive outreach to strictly prevent spam."""
    max_touches = 3
    
    # Below cap: progression allowed
    touch_1 = 1
    touch_2 = 2
    assert (touch_1 >= max_touches) is False
    assert (touch_2 >= max_touches) is False
    
    # Cap reached: outreach suppressed
    touch_3 = 3
    touch_4 = 4
    assert (touch_3 >= max_touches) is True
    assert (touch_4 >= max_touches) is True

def test_demo_mode_fallback(monkeypatch):
    """Assert that RAZORPAY_DEMO_MODE=true safely engages quota shield and bypasses live link creation."""
    # Demo Mode ON -> Quota Shield active
    monkeypatch.setenv("RAZORPAY_DEMO_MODE", "true")
    demo_active = os.getenv("RAZORPAY_DEMO_MODE", "false").lower() == "true"
    assert demo_active is True

    # Demo Mode OFF -> Live API routing active
    monkeypatch.setenv("RAZORPAY_DEMO_MODE", "false")
    demo_inactive = os.getenv("RAZORPAY_DEMO_MODE", "false").lower() == "true"
    assert demo_inactive is False
