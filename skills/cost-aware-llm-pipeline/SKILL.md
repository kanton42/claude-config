---
name: cost-aware-llm-pipeline
description: >
  Cost/latency optimization for apps that call LLM APIs — model routing by task complexity, budget guards,
  narrow retry, and prompt caching. Use when building or tuning LLM calls in any pipeline (signal
  generation, batch processing, or any multi-model workflow), or staying under a spend cap. Directly
  relevant to a shared LLM provider daily budget cap that can exhaust silently (429/403).
  Trigger on: "LLM cost", "model routing", "which model for this", "API budget", "rate limit / 403",
  "prompt caching", "batch LLM", "reduce token spend in <app>". Adapted from ECC (affaan-m/ECC, MIT).
---

# Cost-Aware LLM Pipeline

Control LLM spend without losing quality, by composing four independent levers. Build pipelines so they
degrade gracefully and stay cheap. If multiple apps share a single provider key against a daily cap,
exhaustion will silently 403/429 all of them — track per-app spend and stop the lower-priority app first.

## 1. Route model by task complexity ✅
Start on the cheapest model; escalate only when complexity crosses a threshold. Current tiers:
`claude-haiku-4-5` (cheap/fast, ~1×) → `claude-sonnet-4-6` (balanced, ~4×) → `claude-opus-4-8` (reasoning,
~5×) → `claude-fable-5` (frontier).
```python
HAIKU, SONNET, OPUS = "claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-8"
def select_model(text_len: int, n_items: int, force: str | None = None) -> str:
    if force: return force
    if text_len >= 10_000 or n_items >= 30: return SONNET   # complex
    return HAIKU                                             # simple → 3–4× cheaper
```
Reserve Opus/Fable for genuine reasoning (the decide step), not enrichment/formatting. Log every routing
decision so thresholds can be tuned from real data (a central per-call cost log is the model).

## 2. Budget guard (fail early, not silently) ✅
Track cumulative spend with an immutable tracker; **check before the call**, raise before you blow the cap.
```python
@dataclass(frozen=True, slots=True)
class CostTracker:
    budget_usd: float = 1.00
    spent: float = 0.0
    def add(self, usd): return replace(self, spent=self.spent + usd)
    @property
    def over(self): return self.spent > self.budget_usd
```
For a shared provider key: track per-app daily spend and **stop the lower-priority app first** rather
than letting both exhaust. Surface "budget exhausted" as a visible state, never a silent empty result.

## 3. Narrow retry ✅
Retry only transient errors (connection, rate-limit, 5xx) with exponential backoff; **fail fast** on auth/
bad-request (retrying those just burns budget). `_RETRYABLE = (APIConnectionError, RateLimitError, InternalServerError)`.

## 4. Prompt caching ✅
Mark the stable prefix (system prompt, tool defs, long static context) with `cache_control: ephemeral`;
cache reads ≈ 0.1× input cost, 5-min TTL. Put stable content first, variable input last (see
`working-with-claude` §4). Worth it for any system prompt >1024 tokens — saves cost *and* latency.

## Best practices / anti-patterns
- ✅ cheapest-first + threshold escalation · explicit budget before batches · log routing · cache long prefixes.
- ✅ concise output instructions ("answer in N lines") — output tokens are 4–5× input price.
- ✗ one expensive model for everything · retry on auth/validation errors · mutating cost state · hardcoded
  model strings scattered in code (use constants/config) · ignoring caching on repeated system prompts.

## Sources
Adapted from ECC `skills/cost-aware-llm-pipeline` (MIT); model tiers/caching per the installed `claude-api`
+ `working-with-claude` skills; budget framing from practical cost-telemetry experience with shared provider keys.
