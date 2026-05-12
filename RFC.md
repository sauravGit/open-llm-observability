# RFC-0001: LLM Observability Normalization Layer for OpenTelemetry GenAI

**Status:** Draft v0.4  
**Author:** sauravGit  
**Date:** 2026-05-12  
**License:** Apache 2.0  
**Discussion:** https://github.com/sauravGit/open-llm-observability/discussions/1  
**Upstream:** https://github.com/open-telemetry/semantic-conventions-genai/issues/101  
**Spec:** https://github.com/sauravGit/open-llm-observability/blob/main/RFC.md

---

## Change Log

| Version | Date | Key Changes |
|---------|------|-------------|
| v0.4 | 2026-05-12 | Formalized reconciliation with OTel GenAI client spec; clarified normalization vs. extension boundary; added TTFT streaming attribute; resolved cost unit recommendation; added agent/tool-call span naming convention; expanded migration shims to 5 platforms |
| v0.3 | 2026-05-06 | Reframed as normalization/migration layer; added OpenInference mappings; moved cost to optional extension pack; consolidated upstream OTel issues |
| v0.2 | 2026-05-04 | Added extension packs (RAG, Agents, Eval, Safety); sync SDK metrics.py |
| v0.1 | 2026-05-02 | Initial spec: core metrics, span attributes, KPIs |

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
12. [Agent & Tool-Call Span Naming](#agent--tool-call-span-naming)
13. [Upstream Path to OpenTelemetry](#upstream-path-to-opentelemetry)
14. [Versioning and Evolution Policy](#versioning-and-evolution-policy)
15. [Open Questions for the Community](#open-questions-for-the-community)
16. [Contributing](#contributing)

---

## 1. Abstract

This RFC defines a **vendor-neutral, OpenTelemetry-compatible normalization layer** for LLM observability. It does not propose a parallel standard; instead, it formalizes a consistent schema that extends and reconciles existing OTel GenAI semantic conventions (`gen_ai.client.operation.duration`, `gen_ai.server.time_to_first_token`, `gen_ai.client.token.usage`) into a complete, interoperable client-side metric set.

**This spec is a normalization and migration layer**, not a 
---

## 2. The Fragmentation Problem

Every LLM platform and observability tool today uses different field names, KPI definitions, and export formats. Developers who want end-to-end visibility across multiple providers or backends have to re-instrument every time.

| Signal | OpenLLMetry | Langfuse | OpenInference | Arize Phoenix | AWS Bedrock | Canonical (`gen_ai.*`) |
|--------|-------------|----------|---------------|---------------|-------------|------------------------|
| E2E latency | `llm.request.duration` (ms) | `observation.latency` (ms) | `llm.latency` | `llm.latency_ms` | `FirstByteLatency` + `TotalInferenceTime` | `gen_ai.client.operation.duration` (s) |
| Input tokens | `llm.usage.prompt_tokens` | `usage.input` | `llm.token_count.prompt` | `llm.token_count.prompt` | `InputTokenCount` | `gen_ai.usage.input_tokens` |
| Output tokens | `llm.usage.completion_tokens` | `usage.output` | `llm.token_count.completion` | `llm.token_count.completion` | `OutputTokenCount` | `gen_ai.usage.output_tokens` |
| Cost | `llm.usage.total_cost` | `usage.totalCost` | `llm.cost.total` | (proxy) | CloudWatch custom metric | `gen_ai.usage.cost` (optional) |
| TTFT | (none) | (none) | (none) | (none) | `TimeToFirstByte` | `gen_ai.client.time_to_first_token` |
| Errors | (none) | `error_count` | (none) | (none) | `ThrottlingException` | `gen_ai.client.error_count` |
| Retries | (none) | (none) | (none) | (none) | (none) | `gen_ai.client.retry_count` |
| Rate limits | (none) | (none) | (none) | (none) | `ThrottlingException` | `gen_ai.client.rate_limit.events` |

This fragmentation means dashboards, alerts, and ML pipelines cannot be ported between tools without custom transforms.

---

## 3. Prior Art and Precedent

This spec builds on established work:

- **OpenTelemetry GenAI Semantic Conventions** — The upstream `gen_ai.client.*` and `gen_ai.server.*` namespaces are the foundation. This RFC maps into them, not around them.
- **OpenInference** — Arize's cross-platform tracing convention (`llm.*`) is the most widely adopted fragmentation pattern to normalize.
- **Langfuse Observability** — Popular open-source LLM observability platform with its own schema.
- **OpenLLMetry (Traceloop)** — Early open-source standardization attempt using `llm.*` prefix.
- **AWS Bedrock Telemetry** — CloudWatch-based instrumentation for Bedrock model invocations.

This RFC's contribution: a complete, reconciled mapping that implementers can use as a drop-in normalization shim.

---

## 4. Scope

**In scope (Core - REQUIRED):**
- Request/response latency (`gen_ai.client.operation.duration`)
- Token usage: input, output, total (`gen_ai.usage.input_tokens`, `.output_tokens`, `.total_tokens`)
- Time-to-first-token for streaming (`gen_ai.client.time_to_first_token`)
- Per-request error signaling (`gen_ai.client.error_count`)
- Retry attempt counts (`gen_ai.client.retry_count`)
- Rate-limit event signals (`gen_ai.client.rate_limit.events`)

**In scope (Extension packs):**
- Cost tracking (`gen_ai.usage.cost`)
- RAG signals (retrieval latency, document counts, reranking scores)
- Agent/tool-call tracing (step counts, tool invocations, agent duration)
- Eval/guardrail scores

**Out of scope:**
- Training/fine-tuning job telemetry (separate OTel GenAI area)
- Model provider-specific attributes (covered by `gen_ai.system`)
- Distributed tracing span hierarchy beyond LLM-specific spans

---

## 5. Canonical Metric Schema

### 5.1 Core Metrics (REQUIRED)

| Metric | Instrument | Unit | Description |
|--------|------------|------|-------------|
| `gen_ai.client.operation.duration` | Histogram | `s` | End-to-end request latency |
| `gen_ai.client.time_to_first_token` | Histogram | `s` | Streaming-only: time until first token |
| `gen_ai.usage.input_tokens` | Counter | `{token}` | Prompt/input tokens |
| `gen_ai.usage.output_tokens` | Counter | `{token}` | Completion/output tokens |
| `gen_ai.usage.total_tokens` | Counter | `{token}` | Sum of input + output tokens |
| `gen_ai.client.error_count` | Counter | `{error}` | Per-request error signaling |
| `gen_ai.client.retry_count` | Counter | `{retry}` | Retry attempts |
| `gen_ai.client.rate_limit.events` | Counter | `{event}` | HTTP 429 / throttling events |

### 5.2 Required Resource Attributes

| Attribute | Requirement | Description |
|-----------|-------------|-------------|
| `gen_ai.system` | Required | Provider identifier (e.g., `openai`, `anthropic`, `bedrock`) |
| `gen_ai.request.model` | Required | Model name/version |
| `gen_ai.operation.name` | Required | Operation type (`chat`, `completion`, `embedding`) |
| `deployment.environment` | Recommended | Deployment environment |
| `service.name` | Recommended | Application/service name |

### 5.3 Recommended Span Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `gen_ai.prompt.0.role` | string | Role of message 0 (`system`, `user`, `assistant`) |
| `gen_ai.prompt.0.content` | string | Content of message 0 |
| `gen_ai.completion.0.finish_reason` | string | Model's finish reason (`stop`, `length`, `tool_calls`) |
| `gen_ai.response.model` | string | Actual model used (may differ from request) |
| `gen_ai.usage.completion_tokens` | int | Mirror of output_tokens for compatibility |

---

## 6. Required Span Attributes

This section consolidates the OTel GenAI conventions with LLM-specific extensions.

### 6.1 On Every LLM Span

| Attribute | Requirement | Source |
|-----------|-------------|--------|
| `gen_ai.system` | MUST | OTel GenAI spec |
| `gen_ai.request.model` | MUST | OTel GenAI spec |
| `gen_ai.operation.name` | MUST | OTel GenAI spec |
| `gen_ai.response.model` | SHOULD | OTel GenAI spec (post-response) |

### 6.2 On Chat/Completion Spans

| Attribute | Requirement | Description |
|-----------|-------------|-------------|
| `gen_ai.prompt.*` | SHOULD | Message sequence |
| `gen_ai.completion.*` | SHOULD | Response content and metadata |
| `gen_ai.usage.input_tokens` | MUST | Token count |
| `gen_ai.usage.output_tokens` | MUST | Token count |
| `gen_ai.request.stream` | SHOULD | Boolean; true for streaming calls |
| `gen_ai.request.temperature` | OPTIONAL | Sampling temperature |
| `gen_ai.request.max_tokens` | OPTIONAL | Max output tokens |
| `gen_ai.request.top_p` | OPTIONAL | Top-p sampling |

---

## 7. Derived KPIs and Formulas

Derived KPIs are computed from raw metrics and should not be emitted directly.

| KPI | Formula | Bucket |
|-----|---------|--------|
| Cost per 1K output tokens | `gen_ai.usage.cost / (gen_ai.usage.output_tokens / 1000)` | Cost (extension) |
| Token efficiency ratio | `gen_ai.usage.output_tokens / gen_ai.usage.input_tokens` | Efficiency |
| Error rate % | `(sum(gen_ai.client.error_count) / sum(request_count)) * 100` | Reliability |
| P95 latency | `histogram_quantile(0.95, gen_ai.client.operation.duration)` | Performance |
| P99 latency | `histogram_quantile(0.99, gen_ai.client.operation.duration)` | Performance |
| Retry rate | `sum(gen_ai.client.retry_count) / sum(request_count)` | Reliability |
| Rate-limit rate | `sum(gen_ai.client.rate_limit.events) / sum(request_count)` | Throttling |
| Token throughput | `sum(gen_ai.usage.total_tokens) / elapsed_time` | Efficiency |
| TTFT P95 | `histogram_quantile(0.95, gen_ai.client.time_to_first_token)` | Streaming |

---

## 8. Extension Packs

### 8.1 Cost Extension

| Metric | Instrument | Unit | Description |
|--------|------------|------|-------------|
| `gen_ai.usage.cost` | Counter | `{microdollar}` | Estimated request cost in microdollars |
| `gen_ai.usage.cost.models` | Counter (per-label) | `{microdollar}` | Cost broken down by input vs output |

**Recommendation:** Emit cost as `{microdollar}` (integer) rather than `usd` (float) for precision and to avoid floating-point rounding errors in aggregation. Microdollars provide 6 decimal places of USD precision.

### 8.2 RAG Extension

| Metric | Instrument | Unit | Description |
|--------|------------|------|-------------|
| `gen_ai.rag.retrieval.duration` | Histogram | `s` | Vector DB retrieval latency |
| `gen_ai.rag.documents.retrieved` | Histogram | `{doc}` | Documents retrieved per query |
| `gen_ai.rag.rerank.score` | Histogram | `1` | Reranking score (0-1) |
| `gen_ai.rag.context.precision` | Gauge | `1` | Precision of retrieved context |

### 8.3 Agent Extension

| Metric | Instrument | Unit | Description |
|--------|------------|------|-------------|
| `gen_ai.agent.steps` | Histogram | `{step}` | Number of agent steps per task |
| `gen_ai.agent.tool_calls` | Counter | `{call}` | Tool/function calls made |
| `gen_ai.agent.task.duration` | Histogram | `s` | Total agent task duration |
| `gen_ai.agent.loop.iterations` | Gauge | `{iter}` | Current loop iteration count |

### 8.4 Eval Extension

| Metric | Instrument | Unit | Description |
|--------|------------|------|-------------|
| `gen_ai.eval.score` | Gauge | `1` | Evaluation score (0-1) |
| `gen_ai.eval.latency` | Histogram | `s` | Time to run evaluation |
| `gen_ai.eval.groundedness` | Gauge | `1` | Response groundedness score |

### 8.5 Safety Extension

| Metric | Instrument | Unit | Description |
|--------|------------|------|-------------|
| `gen_ai.safety.flag_count` | Counter | `{flag}` | Safety flag triggers |
| `gen_ai.safety.filtered_tokens` | Counter | `{token}` | Tokens filtered/redacted |

---

## 9. Migration Guide

Use these transforms to normalize existing instrumentation to canonical `gen_ai.*` names.

### 9.1 OpenLLMetry to Canonical

| OpenLLMetry | Canonical | Transform |
|-------------|-----------|----------|
| `llm.request.duration` | `gen_ai.client.operation.duration` | `/1000` (ms to s) |
| `llm.usage.prompt_tokens` | `gen_ai.usage.input_tokens` | 1:1 |
| `llm.usage.completion_tokens` | `gen_ai.usage.output_tokens` | 1:1 |
| `llm.usage.total_cost` | `gen_ai.usage.cost` | `*1_000_000` (USD to microdollars) |
| `llm.request.model` | `gen_ai.request.model` | 1:1 |
| `llm.system` | `gen_ai.system` | 1:1 |

### 9.2 Langfuse to Canonical

| Langfuse | Canonical | Transform |
|----------|-----------|----------|
| `observation.latency` (ms) | `gen_ai.client.operation.duration` | `/1000` |
| `usage.input` | `gen_ai.usage.input_tokens` | 1:1 |
| `usage.output` | `gen_ai.usage.output_tokens` | 1:1 |
| `usage.totalCost` | `gen_ai.usage.cost` | `*1_000_000` |
| `generation.model` | `gen_ai.request.model` | 1:1 |

### 9.3 OpenInference to Canonical

| OpenInference | Canonical | Transform |
|---------------|-----------|----------|
| `llm.latency` | `gen_ai.client.operation.duration` | `/1000` |
| `llm.token_count.prompt` | `gen_ai.usage.input_tokens` | 1:1 |
| `llm.token_count.completion` | `gen_ai.usage.output_tokens` | 1:1 |
| `llm.cost.total` | `gen_ai.usage.cost` | `*1_000_000` |

### 9.4 Arize Phoenix to Canonical

| Phoenix | Canonical | Transform |
|---------|-----------|----------|
| `llm.latency_ms` | `gen_ai.client.operation.duration` | `/1000` |
| `llm.token_count.prompt` | `gen_ai.usage.input_tokens` | 1:1 |
| `llm.token_count.completion` | `gen_ai.usage.output_tokens` | 1:1 |

### 9.5 AWS Bedrock to Canonical

| Bedrock | Canonical | Transform |
|---------|-----------|----------|
| `inputTokenCount` | `gen_ai.usage.input_tokens` | 1:1 |
| `outputTokenCount` | `gen_ai.usage.output_tokens` | 1:1 |
| `TotalInferenceTime` | `gen_ai.client.operation.duration` | `/1000` |
| `TimeToFirstByte` | `gen_ai.client.time_to_first_token` | `/1000` |
| `ThrottlingException` count | `gen_ai.client.rate_limit.events` | 1:1 |

> **SHOULD** implementers provide a shimming layer that automatically maps known source schemas to canonical names at ingestion time.

---

## 10. Working SDK Examples

See the reference Python SDK at [`sdk/python/`](https://github.com/sauravGit/open-llm-observability/tree/main/sdk/python).

### 10.1 Quick Start (Python)

```python
from open_llm_obs import LLMTracer, LLMetrics

# Initialize with your trace provider
tracer = LLMTracer(service_name="my-llm-app")
metrics = LLMetrics()

# Instrument an LLM call
with tracer.trace_llm(operation="chat", model="gpt-4", system="openai") as span:
    span.set_prompt(messages)
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=500,
        stream=False
    )
    
    span.set_completion(
        content=response.choices[0].message.content,
        finish_reason=response.choices[0].finish_reason,
        model=response.model
    )
    
    metrics.record_tokens(
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        total_tokens=response.usage.total_tokens
    )
    
    metrics.record_latency(response.usage.completion_tokens / 1000)  # approximate s
```

### 10.2 Streaming Example

```python
from open_llm_obs import LLMTracer, LLMetrics

tracer = LLMTracer(service_name="streaming-app")
metrics = LLMetrics()

with tracer.trace_llm(operation="chat", model="gpt-4", system="openai") as span:
    span.set_attribute("gen_ai.request.stream", True)
    
    stream = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        stream=True
    )
    
    first_token_time = None
    content_parts = []
    
    for chunk in stream:
        if first_token_time is None:
            metrics.record_ttft(time.time() - request_start)  # Record TTFT
            first_token_time = time.time()
        
        if chunk.choices[0].delta.content:
            content_parts.append(chunk.choices[0].delta.content)
    
    span.set_completion(
        content="".join(content_parts),
        finish_reason=chunk.choices[0].finish_reason,
        model=chunk.model
    )
```

---

## 11. Dashboard Templates

### 11.1 Core Observability Dashboard

A Grafana dashboard is provided at [`dashboards/grafana/gen_ai_core.json`](https://github.com/sauravGit/open-llm-observability/tree/main/dashboards/grafana).

**Panels:**
1. Request rate (RPS) over time
2. P50/P95/P99 latency histograms
3. Token usage: input vs output over time
4. Error rate and retry rate
5. Cost per request (requires cost extension)
6. TTFT for streaming endpoints
7. Model/system breakdown

### 11.2 Alert Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| High latency | P95 > 10s for 5m | Warning |
| Latency spike | P95 > 30s for 2m | Critical |
| Error surge | Error rate > 5% for 5m | Critical |
| Rate limit hit | rate_limit.events > 10/m | Warning |
| Cost anomaly | Cost/request > 3x baseline | Warning |
| TTFT degradation | P95 TTFT > 2s for 5m | Warning |

---

## 12. Agent & Tool-Call Span Naming

**NEW in v0.4**

When tracing agentic workloads, spans should follow this naming convention:

| Span Type | Span Name Pattern | Required Attributes |
|-----------|-------------------|--------------------|
| Chat/Completion | `gen_ai.chat.completion` | `gen_ai.system`, `gen_ai.request.model` |
| Embedding | `gen_ai.embedding` | `gen_ai.system`, `gen_ai.request.model` |
| Agent Task | `gen_ai.agent.run` | `gen_ai.agent.id`, `gen_ai.agent.task` |
| Agent Step | `gen_ai.agent.step` | `gen_ai.agent.step.id`, `gen_ai.agent.tool.name` |
| Tool Call | `gen_ai.tool.call` | `gen_ai.tool.name`, `gen_ai.tool.type` |
| RAG Retrieval | `gen_ai.rag.retrieve` | `gen_ai.rag.query`, `gen_ai.rag.collection` |
| RAG Rerank | `gen_ai.rag.rerank` | `gen_ai.rag.collection` |

**Parent-Child Hierarchy:**
```
gen_ai.agent.run
├── gen_ai.rag.retrieve
│   ├── gen_ai.tool.call (vector_db_query)
├── gen_ai.chat.completion
├── gen_ai.tool.call (search_api)
├── gen_ai.chat.completion (reflection)
└── gen_ai.rag.retrieve (final)
```

> **SHOULD** every agent step span include `gen_ai.agent.step.reason` explaining why that step was taken.

---

## 13. Upstream Path to OpenTelemetry

This RFC is filed as **OTel GenAI Issue #101**: [Proposal: Define a complete, stable gen_ai client metric set](https://github.com/open-telemetry/semantic-conventions-genai/issues/101).

**Alignment with OTel GenAI spec:**

| Proposed Canonical | OTel GenAI Spec | Status |
|--------------------|-----------------|--------|
| `gen_ai.client.operation.duration` | `gen_ai.client.operation.duration` | Already defined; adopt as-is |
| `gen_ai.client.time_to_first_token` | `gen_ai.server.time_to_first_token` | Reconcile: client-side vs server-side distinction |
| `gen_ai.usage.input_tokens` | `gen_ai.client.token.usage` (proposed) | Needs explicit `input`/`output`/`total` fields |
| `gen_ai.usage.output_tokens` | (not yet defined) | NEW proposal |
| `gen_ai.usage.total_tokens` | (not yet defined) | NEW proposal |
| `gen_ai.usage.cost` | (not yet defined) | NEW proposal (extension pack) |
| `gen_ai.client.error_count` | (not yet defined) | NEW proposal |
| `gen_ai.client.retry_count` | (not yet defined) | NEW proposal |
| `gen_ai.client.rate_limit.events` | (not yet defined) | NEW proposal |
| `gen_ai.request.stream` | (not yet defined) | NEW proposal (v0.4) |

**Path to standardization:**
1. SIG discussion and alignment on the consolidation proposal (Issue #101)
2. Once consensus is reached, open a PR against `semantic-conventions-genai` to add new client-side attributes
3. This RFC serves as the reference implementation for adopters during the transition period

---

## 14. Versioning and Evolution Policy

**Specification Versioning:**

| Status | Meaning | Breaking Changes Allowed |
|--------|---------|-------------------------|
| Draft | Experimental; subject to change | Yes |
| Candidate | Proposed for standardization; stable | No |
| Final | Adopted by OTel GenAI SIG | No |

**Backward Compatibility:**
- Canonical metric names, once published at Candidate status, MUST NOT be removed or renamed
- New fields may be added as OPTIONAL before becoming REQUIRED in a future version
- Breaking changes require a new version of the spec and at least 6 months deprecation notice

**SDK Versioning:**
- SDK follows semantic versioning (MAJOR.MINOR.PATCH)
- Current SDK version: `0.4.0` (aligns with RFC v0.4)

---

## 15. Open Questions for the Community

| # | Question | Current Status (v0.4) |
|---|----------|----------------------|
| 1 | **Cost unit:** `{microdollar}` integer vs `usd` float? | RECOMMENDATION: `{microdollar}` for precision. Awaiting SIG input. |
| 2 | **Error rate instrument:** Counter (events) vs Gauge (rate)? | RESOLVED: Use Counter for events; compute rate as derived KPI. |
| 3 | **TTFT streaming attribute:** Add `gen_ai.request.stream` boolean? | RESOLVED in v0.4: Yes, MUST on streaming spans. |
| 4 | **Cost in core vs extension pack?** | RESOLVED: Extension pack only. Not all providers publish pricing. |
| 5 | **OpenInference mapping normativity:** MUST or SHOULD? | RECOMMENDATION: SHOULD for interoperability, MUST for conformance badge. |
| 6 | **Agent/tool-call span naming convention:** Standard format needed? | RESOLVED in v0.4: `gen_ai.agent.*` and `gen_ai.tool.*` patterns defined. |
| 7 | **RAG retrieval: include relevance/recall metrics in spec?** | PENDING: Currently in RAG extension pack as SHOULD. Open for feedback. |

Drop a comment on the [RFC discussion](https://github.com/sauravGit/open-llm-observability/discussions/1) or reply to [OTel GenAI #101](https://github.com/open-telemetry/semantic-conventions-genai/issues/101) to weigh in.

---

## 16. Contributing

This is an open community effort. Here's how to get involved:

### 16.1 Ways to Contribute

- **Use the spec:** Instrument your LLM app with the Python SDK and share feedback
- **Report issues:** Found a gap in the schema? Open an issue on this repo
- **Submit PRs:** Add migration shims, SDK improvements, or dashboard templates
- **Share with your team/tool:** If you use OpenLLMetry, Langfuse, Phoenix, or Bedrock, try the normalization layer
- **Engage with OTel GenAI:** Weigh in on Issue #101 for upstream standardization

### 16.2 Feedback Questions for Early Adopters

- Does the core metric set cover your use cases?
- Which migration shim would be most valuable (OpenLLMetry, Langfuse, OpenInference, Phoenix, Bedrock)?
- Would you contribute a TypeScript SDK implementation?
- Are the extension packs (RAG, Agent, Eval, Safety) useful, or do you need more/less?
- What dashboard metrics do you actually care about in production?
- Would migration from your current tool (Langfuse, OpenLLMetry, Phoenix, Bedrock) to canonical names be straightforward?
- Any signals you wish existed but are missing from the current schema?

### 16.3 Governance

- Maintainer: sauravGit
- License: [Apache 2.0](https://github.com/sauravGit/open-llm-observability/blob/main/LICENSE) (code), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (spec)
- Decision-making: Community consensus via GitHub discussions and issues
- Roadmap: Posted in GitHub Discussions and updated quarterly

---

*This RFC is a living document. Version history and changelog are tracked at the top of this file.*
*Last updated: 2026-05-12*replacement. It maps fragmented observability implementations across OpenLLMetry, Langfuse, OpenInference, Arize Phoenix, AWS Bedrock, and similar tools into canonical `gen_ai.*` semantic names.

