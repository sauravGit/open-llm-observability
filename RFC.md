# RFC-0001: LLM Observability Normalization Layer for OpenTelemetry GenAI

**Status:** Draft v0.3
**Author:** sauravGit
**Date:** 2026-05-06
**License:** Apache 2.0
**Discussion:** https://github.com/sauravGit/open-llm-observability/discussions/1
**Upstream:** https://github.com/open-telemetry/semantic-conventions-genai/issues/101

---

## Table of Contents

1. [Abstract](#abstract)
2. [The Fragmentation Problem](#the-fragmentation-problem)
3. [Prior Art and Precedent](#prior-art-and-precedent)
4. [Scope](#scope)
5. [Canonical Metric Schema](#canonical-metric-schema)
6. [Required Span Attributes](#required-span-attributes)
7. [Derived KPIs and Formulas](#derived-kpis-and-formulas)
8. [Extension Packs](#extension-packs)
9. [Migration Guide](#migration-guide)
10. [Working SDK Examples](#working-sdk-examples)
11. [Dashboard Templates](#dashboard-templates)
12. [Real-World Use Cases](#real-world-use-cases)
13. [Upstream Path to OpenTelemetry](#upstream-path-to-opentelemetry)
14. [Versioning and Evolution Policy](#versioning-and-evolution-policy)
15. [Open Questions for the Community](#open-questions-for-the-community)
16. [Contributing](#contributing)

---

## Abstract

This RFC proposes a **normalization and migration layer on top of existing OpenTelemetry GenAI semantic conventions and OpenInference**, not a parallel new standard. OpenTelemetry already defines core GenAI metrics such as `gen_ai.client.operation.duration`, `gen_ai.client.operation.time_to_first_chunk`, `gen_ai.server.time_to_first_token`, and `gen_ai.client.token.usage`. This work extends and consolidates those conventions — adding missing signals (error rate, retry count, rate-limit events), resolving open schema questions (cost unit, TTFT streaming flag, error instrument type), and providing a migration guide from fragmented vendor-specific naming to the canonical `gen_ai.*` namespace.

The goal is to ship a complete, stable client metric set that the OpenTelemetry GenAI SIG can adopt, replacing the current patchwork of per-issue additions with a single coherent surface.

---

## The Fragmentation Problem

Every major LLM observability tool today emits the same core signals under different names, making cross-tool dashboards, alerts, and cost attribution impossible without custom ETL.

| Signal | OpenLLMetry | Langfuse | OpenInference / Arize Phoenix | AWS Bedrock | OTel GenAI (current) |
|---|---|---|---|---|---|
| E2E latency | `llm.request.duration` | `latency` (ms) | `llm.latency` | `InvocationLatency` | `gen_ai.client.operation.duration` (s) |
| Time to first token | — | — | — | `FirstByteLatency` | `gen_ai.server.time_to_first_token` |
| Input tokens | `gen_ai.usage.prompt_tokens` | `usage_details.input` | `llm.token_count.prompt` | `InputTokenCount` | `gen_ai.client.token.usage` {`input`} |
| Output tokens | `gen_ai.usage.completion_tokens` | `usage_details.output` | `llm.token_count.completion` | `OutputTokenCount` | `gen_ai.client.token.usage` {`output`} |
| Cost | `llm.usage.total_cost` | `cost_details.total` | `llm.cost.total` | (derived) | *(not yet standardized)* |
| Error rate | — | — | — | `InvocationErrors` | *(not yet standardized)* |
| Retry count | — | — | — | — | *(not yet standardized)* |
| Rate limit events | — | — | — | `ThrottledInvocations` | *(not yet standardized)* |

**Root cause:** The OTel GenAI semantic conventions exist but are incomplete — TTFT, detailed token usage, cost, error/retry/rate-limit signals are tracked in separate issues (#14, #23, #76, #93) with no unified proposal to resolve them together. This RFC is that unified proposal.

---

## Prior Art and Precedent

This work builds directly on:

- **OTel GenAI semantic conventions** — `gen_ai.client.operation.duration`, `gen_ai.server.time_to_first_token`, `gen_ai.client.token.usage` are already in the spec. This RFC extends them.
- **OpenInference** (Arize Phoenix) — defines `llm.token_count.*`, `llm.latency`, `llm.cost.total`; the migration table above maps these to canonical names.
- **OTel spec discussion #5069** — @trask redirected the community to `semantic-conventions-genai` as the right upstream venue. This RFC was formally filed as issue #101 there.
- **HTTP and RPC conventions** — `http.client.request.duration` uses seconds (s); we follow that precedent for `gen_ai.client.operation.duration`.
- **Prior issues** — #14 (TTFT), #23 (token usage detail), #76 (streaming), #93 (provider attribute on duration) are consolidated here.

---

## Scope

**In scope:**
- Client-side metric instruments for LLM request observability
- Required span/metric attributes
- Derived KPI formulas computable from the canonical schema
- Migration mappings from OpenLLMetry, Langfuse, OpenInference, and Bedrock
- Extension packs for cost, RAG, agent, and eval signals

**Out of scope:**
- Server-side / provider-internal instrumentation
- Trace/span schema beyond attributes needed to correlate with metrics
- ML training or batch inference pipelines

---

## Canonical Metric Schema

All metrics use the `gen_ai.*` namespace, consistent with existing OTel GenAI conventions.

### Core (REQUIRED)

| Metric | Instrument | Unit | Description |
|---|---|---|---|
| `gen_ai.client.operation.duration` | Histogram | `s` | End-to-end request latency. Consistent with OTel HTTP/RPC conventions (`http.client.request.duration` is also in `s`). |
| `gen_ai.client.time_to_first_token` | Histogram | `s` | Streaming-only: time from request start to first token received. SHOULD be omitted for non-streaming calls. |
| `gen_ai.usage.input_tokens` | Counter | `{token}` | Input tokens consumed. Allows backends to compute rate and total from a single instrument. |
| `gen_ai.usage.output_tokens` | Counter | `{token}` | Output tokens generated. |
| `gen_ai.client.error_rate` | Gauge | `1` | Per-request error signal. Alternative: counter pair `gen_ai.client.error_count` + `gen_ai.client.request_count` with ratio computed by backend. Open to SIG preference. |
| `gen_ai.client.retry_count` | Counter | `{retry}` | Incremented on each retry attempt. |
| `gen_ai.client.rate_limit.events` | Counter | `{event}` | Incremented on each HTTP 429 received. |

### Extension: Cost Pack (`gen_ai.cost.*`)

Cost is intentionally moved out of Core REQUIRED because not all providers publish pricing programmatically, and floating-point precision in cumulative counters is an open question.

| Metric | Instrument | Unit | Notes |
|---|---|---|---|
| `gen_ai.usage.cost` | Counter | `{microdollar}` | Integer microdollars to avoid float drift. Alternative: `usd` float. Open question for SIG. |

### Extension: RAG Pack (`gen_ai.rag.*`)

| Metric | Instrument | Unit |
|---|---|---|
| `gen_ai.rag.retrieval.duration` | Histogram | `s` |
| `gen_ai.rag.documents.retrieved` | Histogram | `{document}` |
| `gen_ai.rag.rerank.score` | Gauge | `1` |

### Extension: Agent Pack (`gen_ai.agent.*`)

| Metric | Instrument | Unit |
|---|---|---|
| `gen_ai.agent.steps` | Counter | `{step}` |
| `gen_ai.agent.tool_calls` | Counter | `{call}` |
| `gen_ai.agent.task.duration` | Histogram | `s` |

### Extension: Eval Pack (`gen_ai.eval.*`)

| Metric | Instrument | Unit |
|---|---|---|
| `gen_ai.eval.score` | Gauge | `1` |
| `gen_ai.eval.latency` | Histogram | `s` |

---

## Required Span Attributes

Following the existing OTel GenAI spec pattern:

| Attribute | Requirement |
|---|---|
| `gen_ai.system` | Required |
| `gen_ai.request.model` | Required |
| `gen_ai.operation.name` | Required |
| `gen_ai.response.model` | Recommended |
| `gen_ai.request.max_tokens` | Opt-In |
| `server.address` | Recommended |
| `server.port` | Opt-In |

---

## Derived KPIs and Formulas

These KPIs are computable entirely from the canonical schema above — no vendor-specific fields required.

| KPI | Formula |
|---|---|
| Cost per 1K output tokens | `gen_ai.usage.cost / (gen_ai.usage.output_tokens / 1000)` |
| Token efficiency ratio | `gen_ai.usage.output_tokens / gen_ai.usage.input_tokens` |
| Error rate % | `gen_ai.client.error_count / gen_ai.client.request_count * 100` |
| P95 latency by model | `histogram_quantile(0.95, gen_ai.client.operation.duration{gen_ai.request.model=...})` |
| Retry overhead % | `gen_ai.client.retry_count / gen_ai.client.request_count * 100` |
| TTFT P50 (streaming) | `histogram_quantile(0.50, gen_ai.client.time_to_first_token)` |

---

## Extension Packs

Extension packs are opt-in metric groups for use cases beyond core LLM request observability:

| Pack | Prefix | Use Case |
|---|---|---|
| Cost | `gen_ai.cost.*` | Billing attribution, budget alerts |
| RAG | `gen_ai.rag.*` | Retrieval pipeline observability |
| Agent | `gen_ai.agent.*` | Multi-step agent task tracking |
| Eval | `gen_ai.eval.*` | Quality scoring pipelines |

Extension packs MUST NOT be required by backends that do not support them. Core pack metrics MUST be emitted for any LLM client request.

---

## Migration Guide

### From OpenLLMetry

| OpenLLMetry | Canonical |
|---|---|
| `llm.request.duration` | `gen_ai.client.operation.duration` (convert ms → s) |
| `gen_ai.usage.prompt_tokens` | `gen_ai.usage.input_tokens` |
| `gen_ai.usage.completion_tokens` | `gen_ai.usage.output_tokens` |
| `llm.usage.total_cost` | `gen_ai.usage.cost` (extension) |

### From Langfuse

| Langfuse | Canonical |
|---|---|
| `latency` (ms) | `gen_ai.client.operation.duration` (÷ 1000) |
| `usage_details.input` | `gen_ai.usage.input_tokens` |
| `usage_details.output` | `gen_ai.usage.output_tokens` |
| `cost_details.total` | `gen_ai.usage.cost` (extension) |

### From OpenInference / Arize Phoenix

| OpenInference | Canonical |
|---|---|
| `llm.latency` | `gen_ai.client.operation.duration` |
| `llm.token_count.prompt` | `gen_ai.usage.input_tokens` |
| `llm.token_count.completion` | `gen_ai.usage.output_tokens` |
| `llm.cost.total` | `gen_ai.usage.cost` (extension) |

### From AWS Bedrock CloudWatch

| Bedrock | Canonical |
|---|---|
| `InvocationLatency` | `gen_ai.client.operation.duration` |
| `FirstByteLatency` | `gen_ai.client.time_to_first_token` |
| `InputTokenCount` | `gen_ai.usage.input_tokens` |
| `OutputTokenCount` | `gen_ai.usage.output_tokens` |
| `ThrottledInvocations` | `gen_ai.client.rate_limit.events` |

---

## Working SDK Examples

```python
from open_llm_obs import LLMObserver

obs = LLMObserver(service_name="my-llm-app")

with obs.record_request(
    system="openai",
    model="gpt-4o",
    operation="chat"
) as req:
    response = openai_client.chat.completions.create(...)
    req.set_token_usage(
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens
    )
```

This emits:
- `gen_ai.client.operation.duration` histogram
- `gen_ai.usage.input_tokens` counter
- `gen_ai.usage.output_tokens` counter
- `gen_ai.client.error_rate` gauge (on error)

---

## Dashboard Templates

Prometheus / Grafana queries using canonical metrics:

```promql
# P95 latency by model
histogram_quantile(0.95, rate(gen_ai_client_operation_duration_bucket[5m]))

# Input token rate
rate(gen_ai_usage_input_tokens_total[5m])

# Error rate %
rate(gen_ai_client_error_count_total[5m]) /
rate(gen_ai_client_request_count_total[5m]) * 100

# Rate limit events
rate(gen_ai_client_rate_limit_events_total[5m])
```

---

## Real-World Use Cases

1. **Multi-provider cost attribution** — same dashboard across OpenAI, Anthropic, Bedrock using canonical token + cost metrics
2. **SLA alerting** — P95 latency alert fires regardless of which SDK/provider emits the signal
3. **Streaming quality** — TTFT histogram identifies slow-start providers before users complain
4. **Retry storm detection** — spike in `gen_ai.client.retry_count` surfaces upstream instability
5. **Budget guardrails** — `gen_ai.usage.cost` with `gen_ai.system` label enables per-provider spend limits

---

## Upstream Path to OpenTelemetry

This RFC is filed as **[semantic-conventions-genai issue #101](https://github.com/open-telemetry/semantic-conventions-genai/issues/101)**, consolidating open issues #14, #23, #76, and #93 into a single proposal for SIG review.

The intended path:
1. SIG review and open questions resolved (cost unit, error instrument, TTFT attribute)
2. PR against `open-telemetry/semantic-conventions-genai` with YAML definitions
3. Stability marked `development` → `stable` following OTel lifecycle policy
4. SDK implementations updated to stable names

---

## Versioning and Evolution Policy

- `gen_ai.client.*` core metrics: stable after SIG approval, no breaking renames
- Extension pack metrics: semver-prefixed (`gen_ai.rag.v1.*`), may evolve independently
- Deprecated mappings kept for 2 minor versions before removal
- All changes go through upstream OTel GenAI SIG PR process

---

## Open Questions for the Community

1. **Cost unit:** `usd` (float Counter) vs `{microdollar}` integer Counter to avoid floating-point drift?
2. **Error rate instrument:** Gauge per-request vs counter pair (`error_count` / `total_count`) with ratio computed by backend?
3. **TTFT streaming flag:** Should `gen_ai.client.time_to_first_token` carry a `gen_ai.response.streaming=true` required attribute, or be implied by presence of the metric?
4. **Cost in core vs extension:** Is cost appropriate in the `core/` set, or should it be an optional `gen_ai.cost.*` extension given that not all providers publish pricing programmatically?
5. **OpenInference alignment:** Should migration mappings from OpenInference be normative (MUST follow) or informative (SHOULD follow)?

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Discussion happens in:
- [GitHub Discussions](https://github.com/sauravGit/open-llm-observability/discussions)
- [OTel GenAI SIG issue #101](https://github.com/open-telemetry/semantic-conventions-genai/issues/101)

PRs welcome for:
- Additional migration mappings (Azure OpenAI, Google Vertex AI, Cohere, etc.)
- Extension pack proposals
- SDK implementations in Go, Java, Node.js
- Grafana dashboard JSON exports
