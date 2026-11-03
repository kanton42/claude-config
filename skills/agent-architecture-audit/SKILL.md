---
name: agent-architecture-audit
description: >
  Full-stack diagnostic for agent/LLM applications — audits the 12-layer agent stack for wrapper
  regression, memory pollution, tool-discipline failures, hidden repair loops, and rendering corruption,
  then produces severity-ranked, code-first fixes. Use as a PRE-SHIP gate for any LLM system (signal
  generation, executors, tool-calling/multi-step/memory features), or when "the agent is getting worse",
  a prompt works in isolation but breaks in the wrapper, or you've debugged agent behavior >15 min without
  a root cause. Trigger on: "agent audit", "agent got worse", "tools flaky", "LLM app broken",
  "why is the output weird", "review my agent architecture". Adapted from ECC (MIT).
---

# Agent Architecture Audit

A diagnostic for agent systems that hide failures behind wrapper layers, stale memory, retry loops, or
transport/rendering mutations. Falsify the wrapper before blaming the model. Code-first fixes, not prompt-first.

**Use (esp.) before shipping** any change that touches prompts, tools, memory, or the decide loop; when
behavior degraded after a wrapper change; when the same model is fine in a probe but wrong in prod.

## The 12-layer stack (any layer can corrupt the answer)
1 System prompt (conflicting/bloated instructions) · 2 Session history (stale context) · 3 Long-term memory
(cross-session pollution) · 4 Distillation (compressed artifacts re-entering as facts) · 5 Active recall
(redundant re-summary) · 6 Tool selection (wrong/skipped routing) · 7 Tool execution (hallucinated — claims
to call but doesn't) · 8 Tool interpretation (misread output) · 9 Answer shaping (format corruption) ·
10 Platform rendering (UI/API/CLI mutates a valid answer) · 11 Hidden repair loops (silent 2nd LLM pass) ·
12 Persistence (expired/cached state reused as live evidence).

## Quick diagnostic (answer these)
| Q | If yes → |
|---|----------|
| Can the model skip a required tool and still answer? | tool not **code-gated** |
| Does old conversation/topic appear in new turns? | memory contamination |
| Same info in system prompt AND memory AND history? | context duplication |
| Does a second LLM pass run before delivery? | hidden repair loop |
| Output differs internal-vs-delivered? | rendering corruption |
| "Must use tool X" only in prompt text? | tool-discipline failure |
| Can the agent's own monologue become persistent memory? | memory poisoning |

## Evidence collection (grep for anti-patterns — Python/TS stack)
```bash
rg "must.*tool|required.*call" -t md            # tool rules only in prose
rg "tool_call|tool_use|messages\.create|llm\.invoke" -t py -t ts   # exec + hidden LLM calls
rg "fallback|retry.*llm|re-?prompt|repair" -t py -t ts             # silent repair loops
rg "memory.*admit|persist.*memory|long.*term.*update" -t py -t ts  # memory admission
rg "rewrite.*response|transform.*output|mutate" -t py -t ts        # output mutation
```
For each finding record: symptom · mechanism · source layer · root cause · evidence `file:line` · confidence (0–1).

## Fix order (code-first)
1 Code-gate tool requirements (enforce in code, not prompt) → 2 Remove/narrow hidden repair agents (make
fallback explicit) → 3 Cut context duplication (same info via prompt+history+memory+distillation) → 4 Tighten
memory admission (user corrections > agent assertions) → 5 Tighten distillation triggers → 6 Reduce rendering
mutation (pass-through) → 7 Typed JSON envelopes over freeform prose internally.

## Severity → action
`critical` (confidently wrong operational behavior) fix before release · `high` (frequent degradation) this
sprint · `medium` (fragile/wasteful) next cycle · `low` (cosmetic) backlog.

## Output
Lead with **severity-ranked findings** (most critical first), then the architecture diagnosis (which layer
corrupted what, why), then an ordered code-first fix plan. Be direct — if it's broken, say so; no compliment
preamble. Don't let a clean *current* state erase a dirty historical incident; don't trust markdown prose as
an internal protocol; don't accept "must use tool" that code never enforces.

## Sources
Adapted from ECC `skills/agent-architecture-audit` (MIT, origin "oh-my-agent-check"); pairs with
`code-review-discipline` (evidence/confidence gate) and `working-with-claude` (context engineering).
