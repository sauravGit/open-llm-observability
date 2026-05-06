# RFC-0001: LLM Observability Semantic Conventions for OpenTelemetry

**Status:** Draft v0.2
**Author:** sauravGit
**Date:** 2026-05-06
**License:** Apache 2.0
**Discussion:** https://github.com/sauravGit/open-llm-observability/discussions/1

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

This RFC proposes **new semantic conventions for LLM observability**, following the established pattern of OpenTelemetry HTTP, database, and messaging conventions. It defines a canonical set of metric names, span attributes, resource attributes, and derived KPIs that any LLM SDK, framework, or observability platform can emit and consume without translation.

The goal is not a new tool. The goal is a shared language — so that a team switching from one observability backend to another never has to rewrite a single dashboard.

---

## The Fragmentation Problem

Every major LLM observability tool today defines its own metric names, attribute schemas, and KPI calculations. The result: teams that instrument once cannot portably observe everywhere.

### Metric Name Fragmentation Table

| Signal | OpenLLMetry | Langfuse | Arize Phoenix | AWS Bedrock | **This Proposal** |
|---|---|---|---|---|---|
| Request latency | `llm.request.duration` | `observation.latency` | `llm.latency_ms` | `invocation_latency` | `gen_ai.client.operation.duration` |
| Time to first token | `llm.time_to_first_token` | *(not standard)* | `llm.ttft_ms` | `first_byte_latency` | `gen_ai.client.time_to_first_token` |
| Input tokens | `llm.usage.prompt_tokens` | `usage.input` | `llm.token_count.prompt` | `input_token_count` | `gen_ai.usage.input_tokens` |
| Output tokens | `llm.usage.completion_tokens` | `usage.output` | `llm.token_count.completion` | `output_token_count` | `gen_ai.usage.output_tokens` |
| Total cost | `llm.usage.total_cost` | `usage.totalCost` | `llm.token_count.total` *(proxy)* | *(not emitted)* | `gen_ai.usage.cost` |
| Error rate | *(counter only)* | *(not standard)* | `llm.error_rate` | `invocation_client_errors` | `gen_ai.client.error_rate` |
| Model name | `gen_ai.request.model` | `model` | `llm.model_name` | `modelId` | `gen_ai.request.model` |
| Provider/system | `gen_ai.system` | `provider` | `llm.system` | *(implicit)* | `gen_ai.system` |

> **The problem is visible.** Eight teams using eight tools emit eight different schemas for the same signals. A Grafana dashboard built on OpenLLMetry breaks the moment you migrate to Phoenix. A cost alert written against Langfuse fields is useless in Bedrock. This RFC proposes a single canonical row that all tools can map to.

---

## Prior Art and Precedent

OpenTelemetry has successfully standardized semantic conventions for other infrastructure domains:

| Domain | Convention Prefix | Status |
|---|---|---|
| HTTP client/server | `http.*` | Stable |
| Database calls | `db.*` | Stable |
| Messaging systems | `messaging.*` | Stable |
| RPC calls | `rpc.*` | Stable |
| GenAI spans | `gen_ai.*` | Development |
| **LLM metrics (this RFC)** | **`gen_ai.*`** | **Proposed** |

This RFC extends the existing `gen_ai.*` span conventions (currently in development in the OpenTelemetry GenAI SIG) with a **complete metric layer** — following the same pattern used for HTTP and database conventions, where span attributes and metric names share a common namespace and vocabulary.

Just as `http.request.duration` was standardized so that any web framework could emit latency data that any backend could consume, `gen_ai.client.operation.duration` should be standardized so that any LLM framework can emit latency data that any observability backend can consume.

---

## Scope

**In scope:**
- Canonical metric names, instrument types, and units
- Required and recommended span attributes
- Resource attributes for LLM services
- Derived KPI formulas
- Extension namespaces for RAG, agents, and safety
- Migration mappings from existing tools
- Interoperability rules for backends

**Out of scope:**
- Prompt/completion content capture (covered separately by the GenAI SIG events spec)
- Evaluation scores and human feedback (proposed as `gen_ai.eval.*` extension pack)
- Vendor-specific attributes beyond the `gen_ai.*` namespace
- Billing or quota management APIs

---

## Canonical Metric Schema

### Core Metrics (REQUIRED)

All compliant instrumentation libraries MUST emit the following metrics.

| Metric Name | Instrument | Unit | Description |
|---|---|---|---|
| `gen_ai.client.operation.duration` | Histogram | `s` | End-to-end latency from request sent to last response byte received |
| `gen_ai.client.time_to_first_token` | Histogram | `s` | Time from request sent to first response token received (streaming only) |
| `gen_ai.usage.input_tokens` | Counter | `{token}` | Number of tokens in the input/prompt |
| `gen_ai.usage.output_tokens` | Counter | `{token}` | Number of tokens in the model response |
| `gen_ai.usage.cost` | Counter | `usd` | Estimated cost of the request in USD |
| `gen_ai.client.error_rate` | Gauge | `1` | Ratio of failed requests to total requests (rolling 1-min window) |
| `gen_ai.client.retry_count` | Counter | `{request}` | Number of retry attempts made for throttled or failed requests |
| `gen_ai.client.rate_limit.events` | Counter | `{event}` | Number of rate limit responses (HTTP 429) received from the provider |

### Recommended Histogram Buckets

For `gen_ai.client.operation.duration` and `gen_ai.client.time_to_first_token`:

```
buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
```

These buckets are chosen to capture the full range of LLM response times from fast cached responses (~10ms) to long agentic chains (~60s).

---

## Required Span Attributes

All LLM spans conforming to this convention MUST include the following attributes:

| Attribute | Type | Required | Description | Example |
|---|---|---|---|---|
| `gen_ai.system` | string | REQUIRED | The LLM provider/system | `openai`, `anthropic`, `google`, `aws.bedrock` |
| `gen_ai.operation.name` | string | REQUIRED | The type of LLM operation | `chat`, `completion`, `embeddings`, `image_generation` |
| `gen_ai.request.model` | string | REQUIRED | The model requested by the client | `gpt-4o`, `claude-3-opus`, `gemini-1.5-pro` |
| `gen_ai.response.model` | string | RECOMMENDED | The model that actually responded (may differ from requested) | `gpt-4o-2024-08-06` |
| `gen_ai.request.max_tokens` | int | RECOMMENDED | Maximum tokens requested | `4096` |
| `gen_ai.request.temperature` | double | RECOMMENDED | Sampling temperature | `0.7` |
| `gen_ai.response.finish_reasons` | string[] | RECOMMENDED | Why the response ended | `["stop"]`, `["length"]`, `["tool_calls"]` |
| `error.type` | string | CONDITIONAL | Error class if the request failed | `RateLimitError`, `TimeoutError` |
| `server.address` | string | RECOMMENDED | LLM API endpoint hostname | `api.openai.com` |

### Resource Attributes

| Attribute | Type | Description |
|---|---|---|
| `service.name` | string | Name of the instrumenting service |
| `service.version` | string | Version of the instrumenting service |
| `deployment.environment` | string | `production`, `staging`, `development` |
| `telemetry.sdk.name` | string | Name of the instrumentation library |
| `telemetry.sdk.version` | string | Version of the instrumentation library |

---

## Derived KPIs and Formulas

These KPIs CANNOT be emitted directly as raw metrics but SHOULD be computed by observability backends from the canonical metrics above. Providing these formulas as part of the spec ensures that all backends compute them identically.

### Cost Efficiency

```
cost_per_successful_request =
  sum(gen_ai.usage.cost) / count(successful gen_ai.client.operation.duration)

cost_per_1k_output_tokens =
  (sum(gen_ai.usage.cost) / sum(gen_ai.usage.output_tokens)) * 1000
```

### Token Efficiency

```
token_efficiency =
  sum(gen_ai.usage.output_tokens) / sum(gen_ai.usage.input_tokens)
  -- Values > 1 indicate verbose responses; values < 0.1 may indicate prompt padding

total_tokens_per_request =
  (sum(gen_ai.usage.input_tokens) + sum(gen_ai.usage.output_tokens)) /
  count(gen_ai.client.operation.duration)
```

### Latency

```
ttft_p95 = histogram_quantile(0.95, gen_ai.client.time_to_first_token)

latency_p99 = histogram_quantile(0.99, gen_ai.client.operation.duration)

streaming_overhead =
  gen_ai.client.operation.duration - gen_ai.client.time_to_first_token
  -- Time spent receiving tokens after the first token
```

### Reliability

```
success_rate =
  1 - gen_ai.client.error_rate

retry_amplification_factor =
  sum(gen_ai.client.retry_count) / count(gen_ai.client.operation.duration)
  -- Factor > 1 means retries are adding significant load

rate_limit_pressure =
  sum(gen_ai.client.rate_limit.events) / count(gen_ai.client.operation.duration)
  -- Ratio of rate-limited calls to total calls
```

### RAG-Specific (Extension Pack)

```
retrieval_yield =
  sum(gen_ai.rag.relevant_docs_retrieved) / sum(gen_ai.rag.total_docs_retrieved)
  -- Precision of retrieval; values < 0.5 suggest poor retrieval quality

context_utilization =
  sum(gen_ai.rag.context_tokens_used) / sum(gen_ai.usage.input_tokens)
  -- Fraction of input tokens consumed by retrieved context
```

---

## Extension Packs

The core `gen_ai.*` schema is intentionally minimal. Domain-specific signals are organized into **extension packs** that teams can adopt independently without touching the stable base.

### Pack Structure

```
core/          <- This RFC (stable base, required)
extensions/
  rag/         <- Retrieval-Augmented Generation signals
  agents/      <- Multi-step agent and tool-call signals
  eval/        <- Evaluation scores and human feedback
  safety/      <- Content filtering and guardrail signals
  fine-tuning/ <- Training run and fine-tune job signals
```

### RAG Extension Pack (`gen_ai.rag.*`)

| Metric | Instrument | Unit | Description |
|---|---|---|---|
| `gen_ai.rag.retrieval.duration` | Histogram | `s` | Time spent on document retrieval |
| `gen_ai.rag.total_docs_retrieved` | Counter | `{document}` | Total documents retrieved from the store |
| `gen_ai.rag.relevant_docs_retrieved` | Counter | `{document}` | Documents judged relevant (by reranker or threshold) |
| `gen_ai.rag.context_tokens_used` | Counter | `{token}` | Tokens consumed by retrieved context in the prompt |
| `gen_ai.rag.rerank.duration` | Histogram | `s` | Time spent on reranking (if applicable) |

### Agent Extension Pack (`gen_ai.agent.*`)

| Metric | Instrument | Unit | Description |
|---|---|---|---|
| `gen_ai.agent.steps` | Histogram | `{step}` | Number of reasoning/action steps per agent run |
| `gen_ai.agent.tool_calls` | Counter | `{call}` | Total tool/function calls made |
| `gen_ai.agent.tool_errors` | Counter | `{error}` | Tool calls that returned an error |
| `gen_ai.agent.total_duration` | Histogram | `s` | End-to-end duration of a complete agent run |

### Eval Extension Pack (`gen_ai.eval.*`)

| Metric | Instrument | Unit | Description |
|---|---|---|---|
| `gen_ai.eval.score` | Histogram | `1` | Evaluation score (0–1), labeled by `eval.type` |
| `gen_ai.eval.latency` | Histogram | `s` | Time to run evaluation |

Attributes: `eval.type` = `groundedness`, `relevance`, `faithfulness`, `toxicity`, `hallucination`

---

## Migration Guide

This section provides mapping tables from existing tool-specific metrics to the canonical `gen_ai.*` names.

### From OpenLLMetry

| OpenLLMetry Metric | Canonical Name |
|---|---|
| `llm.request.duration` | `gen_ai.client.operation.duration` |
| `llm.usage.prompt_tokens` | `gen_ai.usage.input_tokens` |
| `llm.usage.completion_tokens` | `gen_ai.usage.output_tokens` |
| `llm.usage.total_cost` | `gen_ai.usage.cost` |
| `llm.time_to_first_token` | `gen_ai.client.time_to_first_token` |

### From Langfuse

| Langfuse Field | Canonical Name |
|---|---|
| `observation.latency` | `gen_ai.client.operation.duration` |
| `usage.input` | `gen_ai.usage.input_tokens` |
| `usage.output` | `gen_ai.usage.output_tokens` |
| `usage.totalCost` | `gen_ai.usage.cost` |

### From Arize Phoenix

| Phoenix Attribute | Canonical Name |
|---|---|
| `llm.latency_ms` | `gen_ai.client.operation.duration` (convert ms→s) |
| `llm.token_count.prompt` | `gen_ai.usage.input_tokens` |
| `llm.token_count.completion` | `gen_ai.usage.output_tokens` |
| `llm.token_count.total` | (derived: input + output) |

### From AWS Bedrock

| Bedrock Attribute | Canonical Name |
|---|---|
| `invocation_latency` | `gen_ai.client.operation.duration` |
| `input_token_count` | `gen_ai.usage.input_tokens` |
| `output_token_count` | `gen_ai.usage.output_tokens` |
| `first_byte_latency` | `gen_ai.client.time_to_first_token` |

### Migration Shim Pattern

SDKs that already emit tool-specific metrics can add a shim layer:

```python
from opentelemetry.sdk.metrics import MeterProvider
from open_llm_observability.shim import LegacyMetricShim

# Automatically maps legacy metric names to gen_ai.* canonical names
shim = LegacyMetricShim(source="openllmetry", meter_provider=MeterProvider())
shim.install()
```

---

## Working SDK Examples

### Python — Minimal Compliant Instrumentation

```python
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider

meter = metrics.get_meter("gen_ai", version="1.0.0")
tracer = trace.get_tracer("gen_ai", tracer_version="1.0.0")

# Core metrics
operation_duration = meter.create_histogram(
    name="gen_ai.client.operation.duration",
    unit="s",
    description="End-to-end latency from request sent to last response byte",
)
time_to_first_token = meter.create_histogram(
    name="gen_ai.client.time_to_first_token",
    unit="s",
    description="Time from request sent to first response token (streaming)",
)
input_tokens = meter.create_counter(
    name="gen_ai.usage.input_tokens",
    unit="{token}",
    description="Number of tokens in the input/prompt",
)
output_tokens = meter.create_counter(
    name="gen_ai.usage.output_tokens",
    unit="{token}",
    description="Number of tokens in the model response",
)
cost = meter.create_counter(
    name="gen_ai.usage.cost",
    unit="usd",
    description="Estimated cost of the request in USD",
)

def call_llm(prompt: str, model: str, system: str = "openai"):
    import time
    import openai

    attrs = {
        "gen_ai.system": system,
        "gen_ai.request.model": model,
        "gen_ai.operation.name": "chat",
    }

    with tracer.start_as_current_span("gen_ai.chat", attributes=attrs) as span:
        t0 = time.perf_counter()
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        duration = time.perf_counter() - t0

        in_tok = response.usage.prompt_tokens
        out_tok = response.usage.completion_tokens
        estimated_cost = (in_tok * 0.000003) + (out_tok * 0.000015)

        operation_duration.record(duration, attrs)
        input_tokens.add(in_tok, attrs)
        output_tokens.add(out_tok, attrs)
        cost.add(estimated_cost, attrs)

        span.set_attribute("gen_ai.response.model", response.model)
        span.set_attribute("gen_ai.usage.input_tokens", in_tok)
        span.set_attribute("gen_ai.usage.output_tokens", out_tok)

        return response.choices[0].message.content
```

### TypeScript — Minimal Compliant Instrumentation

```typescript
import { metrics, trace } from '@opentelemetry/api';

const meter = metrics.getMeter('gen_ai', '1.0.0');
const tracer = trace.getTracer('gen_ai', '1.0.0');

const operationDuration = meter.createHistogram('gen_ai.client.operation.duration', { unit: 's' });
const inputTokens = meter.createCounter('gen_ai.usage.input_tokens', { unit: '{token}' });
const outputTokens = meter.createCounter('gen_ai.usage.output_tokens', { unit: '{token}' });
const cost = meter.createCounter('gen_ai.usage.cost', { unit: 'usd' });

async function callLLM(prompt: string, model: string) {
  const attrs = { 'gen_ai.system': 'openai', 'gen_ai.request.model': model, 'gen_ai.operation.name': 'chat' };
  return tracer.startActiveSpan('gen_ai.chat', { attributes: attrs }, async (span) => {
    const t0 = Date.now();
    const response = await openai.chat.completions.create({ model, messages: [{ role: 'user', content: prompt }] });
    const duration = (Date.now() - t0) / 1000;
    operationDuration.record(duration, attrs);
    inputTokens.add(response.usage!.prompt_tokens, attrs);
    outputTokens.add(response.usage!.completion_tokens, attrs);
    span.end();
    return response.choices[0].message.content;
  });
}
```

---

## Dashboard Templates

Compliant dashboards SHOULD surface the following panels derived from canonical metrics.

### Tier 1 — Operational Health (Always On)

| Panel | Query (PromQL) | Alert Threshold |
|---|---|---|
| P50/P95/P99 Latency | `histogram_quantile(0.95, rate(gen_ai_client_operation_duration_bucket[5m]))` | P95 > 5s |
| Error Rate | `avg(gen_ai_client_error_rate)` | > 1% |
| Token Throughput | `rate(gen_ai_usage_input_tokens_total[1m]) + rate(gen_ai_usage_output_tokens_total[1m])` | — |
| Hourly Cost | `increase(gen_ai_usage_cost_total[1h])` | > budget threshold |
| Rate Limit Events | `rate(gen_ai_client_rate_limit_events_total[5m])` | > 0 sustained |

### Tier 2 — Efficiency KPIs

| Panel | Formula |
|---|---|
| Output/Input Ratio | `rate(output_tokens[5m]) / rate(input_tokens[5m])` |
| Cost per 1K Output Tokens | `rate(cost[5m]) / (rate(output_tokens[5m]) / 1000)` |
| TTFT Percentiles (streaming) | `histogram_quantile(0.95, rate(gen_ai_client_time_to_first_token_bucket[5m]))` |
| Retry Rate | `rate(gen_ai_client_retry_count_total[5m])` |

### Tier 3 — RAG-Specific (when `gen_ai.rag.*` extension is active)

| Panel | Formula |
|---|---|
| Retrieval Latency P95 | `histogram_quantile(0.95, rate(gen_ai_rag_retrieval_duration_bucket[5m]))` |
| Context Recall | `rate(gen_ai_rag_relevant_docs_retrieved_total[5m]) / rate(gen_ai_rag_total_docs_retrieved_total[5m])` |
| Context Token Ratio | `rate(gen_ai_rag_context_tokens_used_total[5m]) / rate(gen_ai_usage_input_tokens_total[5m])` |

### Grafana Dashboard-as-Code

A reference Grafana dashboard JSON is published at `dashboards/grafana/gen_ai_core.json` in this repo.

---

## Real-World Use Cases

### Use Case 1: Multi-Provider Cost Comparison

A team uses GPT-4o for complex tasks and Claude Haiku for simple tasks. With canonical metrics, a single dashboard panel compares cost-per-output-token across providers using the same PromQL query regardless of which SDK is used:

```promql
rate(gen_ai_usage_cost_total[1h])
  / (rate(gen_ai_usage_output_tokens_total[1h]) / 1000)
by (gen_ai_system, gen_ai_request_model)
```

### Use Case 2: RAG Pipeline Quality Monitoring

A team instrumenting a RAG pipeline can track whether retrieval quality is degrading by plotting `gen_ai.rag.relevant_docs_retrieved / gen_ai.rag.total_docs_retrieved` over time. A drop below a threshold triggers an alert to re-tune the retriever.

### Use Case 3: Switching Observability Backends

A startup begins with Langfuse. Six months later they migrate to an internal OTel collector. Because both emit `gen_ai.*` canonical metrics, all dashboards, alerts, and SLO definitions survive the migration without a single rename.

### Use Case 4: Agent Step Budget Enforcement

Using `gen_ai.agent.steps` with an alert on P99 step count prevents runaway agents from consuming unbounded tokens or budget. The alert fires before cost damage occurs.

### Use Case 5: Model Regression Detection

When a model provider silently updates a model version, a spike in `gen_ai.usage.cost` or `gen_ai.client.operation.duration` against a stable `gen_ai.usage.output_tokens` signals the regression without any code change.

---

## Upstream Path to OpenTelemetry

This RFC is designed to be upstreamed into the OpenTelemetry Semantic Conventions as a formal `gen_ai` namespace extension.

### Proposed Upstream Steps

1. **Community RFC** — This document. Gather feedback from SDK authors, observability backends, and end-users.
2. **Proof of Concept** — Implement the schema in at least two instrumentation libraries (e.g., OpenLLMetry and a Python SDK).
3. **OTel SIG Proposal** — Submit a proposal to the [OpenTelemetry GenAI SIG](https://github.com/open-telemetry/community/blob/main/projects/gen-ai.md) with the community consensus document.
4. **Experimental Status** — Merge into `opentelemetry-specification` under `experimental` stability.
5. **Stable Status** — After 6 months of production adoption across ≥3 independent implementations, promote to `stable`.

### Relationship to Existing OTel Work

| Existing OTel Spec | Relationship to This RFC |
|---|---|
| `gen_ai.*` (HTTP semantic conventions) | This RFC extends and specializes for LLM workloads |
| OpenTelemetry GenAI SIG events spec | Complementary — covers prompt/completion content, this covers metrics |
| OTel Metrics API/SDK | Implementation substrate — no conflicts |
| OTel Resource attributes | This RFC adds `gen_ai.service.*` resource attributes |

---

## Versioning and Evolution Policy

### Stability Levels

| Level | Meaning |
|---|---|
| `experimental` | May change; use in dev/staging only |
| `stable` | Backwards-compatible additions only |
| `deprecated` | Supported for 2 major versions then removed |

### Rules for Evolution

- **New metrics** can be added to `core/` only in minor versions after a 30-day RFC comment period.
- **Metric renames** require a 6-month deprecation window with both old and new names emitted simultaneously.
- **Extension packs** are versioned independently from `core/` and may evolve faster.
- **Breaking changes** (attribute removals, unit changes) require a major version bump and a 12-month migration window.
- **Cardinality rules**: No new high-cardinality attributes (e.g., per-user IDs) may be added to `core/` metrics. These belong in spans only.

### Version Compatibility Matrix

```
core/ v1.x is compatible with extension packs published against core/ v1.0+
core/ v2.x introduces a compatibility break; migration guide will be published
```

---

## Open Questions for the Community

We are actively seeking input on the following design decisions:

1. **Cost unit**: Should `gen_ai.usage.cost` use `usd` or a vendor-neutral `{microdollar}` integer to avoid floating-point precision issues in counters?

2. **Error rate instrument**: Is a `Gauge` the right instrument for `gen_ai.client.error_rate`, or should we use a rolling counter pair (`error_count` + `total_count`) and let the backend compute the ratio?

3. **Model version granularity**: Should `gen_ai.request.model` include the full versioned name (e.g., `gpt-4o-2024-08-06`) or normalize to the family name (`gpt-4o`)? Or should both be attributes?

4. **Streaming token accounting**: When using streaming responses, token counts are often not available until the stream ends. Should there be an explicit `gen_ai.streaming` boolean attribute to distinguish accounting modes?

5. **Multi-modal inputs**: How should `gen_ai.usage.input_tokens` account for image tokens in vision models (e.g., GPT-4V, Claude 3)? Separate `gen_ai.usage.input_image_tokens`?

6. **Cache hit tracking**: Providers like Anthropic and OpenAI now offer prompt caching with different pricing. Should we add `gen_ai.usage.cache_read_tokens` and `gen_ai.usage.cache_write_tokens`?

7. **Batch API support**: How should asynchronous batch requests (OpenAI Batch API, Vertex AI batch prediction) be represented? They have fundamentally different latency characteristics.

8. **Extension pack governance**: Who owns extension pack versioning? Should it be centralized in this repo or federated to domain-specific repos?

Please weigh in via [GitHub Discussions](https://github.com/sauravGit/open-llm-observability/discussions).

---

## Contributing

We welcome contributions of all kinds — especially from SDK authors, observability platform engineers, and ML platform teams who have firsthand experience with the fragmentation problem.

### How to Contribute

1. **Comment on the RFC** — Open a [GitHub Discussion](https://github.com/sauravGit/open-llm-observability/discussions) with your feedback.
2. **Propose a new metric** — Open an issue using the [New Metric Proposal](https://github.com/sauravGit/open-llm-observability/issues/new?template=new-metric-proposal.md) template.
3. **Report a schema conflict** — Open an issue using the [Schema Conflict Report](https://github.com/sauravGit/open-llm-observability/issues/new?template=schema-conflict-report.md) template.
4. **Implement an SDK shim** — See `sdk/python/` for the reference implementation. PRs welcome.
5. **Add an extension pack** — Propose a new extension namespace in a Discussion before implementing.

### Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/) Code of Conduct.

### Maintainers

- [@sauravGit](https://github.com/sauravGit) — project lead

### License

This specification is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Reference implementations are licensed under Apache 2.0.

---

*This RFC is a living document. The canonical version is always at [github.com/sauravGit/open-llm-observability/blob/main/RFC.md](https://github.com/sauravGit/open-llm-observability/blob/main/RFC.md).*
