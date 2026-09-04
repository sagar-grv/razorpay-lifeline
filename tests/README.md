# 🧪 Project Lifeline Test Suite

Automated verification tests for compliance guardrails, proactive ladder boundaries, and test-mode quota shielding.

---

## 🏃 Running Tests

Ensure your virtual environment is active and dependencies are installed:

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with quick summary output
pytest tests/ -q
```

---

## 📋 Test Coverage

1. **`test_stop_intent_detection`**:
   - Validates deterministic, zero-hallucination opt-out keyword detection across English and Hindi (e.g., `STOP PLEASE`, `बंद करो`).
   - Ensures conversational non-opt-out customer queries do not trigger false-positive compliance halts.

2. **`test_ladder_cap`**:
   - Validates that proactive multi-touch escalation stops when `touch_count >= 3` to satisfy anti-spam guidelines.

3. **`test_demo_mode_fallback`**:
   - Validates that `RAZORPAY_DEMO_MODE=true` safely shields Razorpay account test link quotas during automated CI/eval runs.
