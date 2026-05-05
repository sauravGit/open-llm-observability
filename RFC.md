# RFC-0001: Universal LLM Observability Semantic Convention
**Status:** Draft v0.1  
**Author:** sauravGit  
**Date:** 2026-05-05  
**License:** Apache 2.0

---

## Abstract

This RFC defines a vendor-neutral, OpenTelemetry-compatible semantic convention
for instrumenting Large Language Model (LLM) applications. It specifies a
canonical set of metric names, span attributes, resource attributes, and derived
KPIs that any LLM SDK, framework, or platform can emit once and export to
any OTEL-compatible observability backend.

---

## Motivation

Every LLM observability platform today invents its own field names, KPI
definitions, and export formats. Developers who want visibility across multiple
providers, frameworks, or backends must re-instrument each time. A single
canonical layer, built on OpenTelemetry, eliminates that cost.

---

## Scope

**In scope:**
- Canonical span names and required/optional span attributes
- Core metric names, types, and units
- Required resource attributes
- Recommended label set
- Derived KPI definitions
- Interoperability rules for providers and backends

**Out of scope (v0.1):**
- Model evaluation metrics (BLEU, ROUGE, etc.)
- Training or fine-tuning telemetry
- Platform-specific configuration

---

## Resource Attributes

| Attribute               | Type   | Required | Description                        |
|-------------------------|--------|----------|------------------------------------|
| service.name            | string | yes      | Name of the instrumented service   |
| service.version         | string | yes      | Version of the service             |
| deployment.environment  | string | yes      | e.g. production, staging, dev      |
| gen_ai.app.name         | string | yes      | Application/product name           |
| gen_ai.app.version      | string | no       | Application version                |
| gen_ai.provider         | string | yes      | e.g. openai, anthropic, google     |
| gen_ai.model            | string | yes      | e.g. gpt-4o, claude-3-5-sonnet     |
| gen_ai.region           | string | no       | Cloud region of the endpoint       |

---

## Span Names

| Span Name            | Description                              |
|----------------------|------------------------------------------|
| gen_ai.request       | A single LLM inference call              |
| gen_ai.stream        | A streaming LLM inference call           |
| gen_ai.tool_call     | A tool/function call within a request    |
| gen_ai.retrieval     | A retrieval step (RAG)                   |
| gen_ai.guardrail     | A safety/policy check                    |
| gen_ai.embedding     | An embedding generation call             |

---

## Required Span Attributes

| Attribute                  | Type    | Description                              |
|----------------------------|---------|------------------------------------------|
| gen_ai.system              | string  | Provider system name                     |
| gen_ai.request.model       | string  | Model name used for request              |
| gen_ai.request.type        | string  | chat, completion, embedding, tool        |
| gen_ai.response.model      | string  | Actual model that served the response    |
| gen_ai.prompt.tokens       | int     | Input token count                        |
| gen_ai.completion.tokens   | int     | Output token count                       |
| gen_ai.total.tokens        | int     | Total tokens consumed                    |
| gen_ai.latency_ms          | float   | End-to-end latency in milliseconds       |
| gen_ai.cost_usd            | float   | Estimated USD cost of the request        |
| gen_ai.error.type          | string  | Error class if request failed            |
| gen_ai.retry.count         | int     | Number of retries attempted              |
| gen_ai.rate_limit.hit      | boolean | Whether a rate limit was encountered     |

---

## Core Metrics

| Metric Name                        | Type      | Unit    | Description                        |
|------------------------------------|-----------|---------|------------------------------------|
| gen_ai.requests.total              | Counter   | {req}   | Total inference requests           |
| gen_ai.requests.errors.total       | Counter   | {req}   | Total failed requests              |
| gen_ai.latency                     | Histogram | ms      | End-to-end request latency         |
| gen_ai.time_to_first_token         | Histogram | ms      | Time to first streaming token      |
| gen_ai.usage.input_tokens          | Histogram | {tok}   | Input token count per request      |
| gen_ai.usage.output_tokens         | Histogram | {tok}   | Output token count per request     |
| gen_ai.usage.total_tokens          | Histogram | {tok}   | Total token count per request      |
| gen_ai.usage.cost                  | Histogram | USD     | Estimated cost per request         |
| gen_ai.tool_calls.total            | Counter   | {call}  | Total tool/function calls          |
| gen_ai.retrieval.docs_returned     | Histogram | {doc}   | Retrieved documents per retrieval  |
| gen_ai.guardrail.violations.total  | Counter   | {viol}  | Total safety/policy violations     |

---

## Recommended Labels

| Label                  | Example values                      |
|------------------------|-------------------------------------|
| gen_ai.system          | openai, anthropic, vertexai         |
| gen_ai.request.model   | gpt-4o, claude-3-5-sonnet           |
| gen_ai.request.route   | /chat, /summarize, /classify        |
| gen_ai.request.type    | chat, embedding, tool               |
| feature                | search, onboarding, support         |
| tenant                 | org-id or tenant-id                 |
| environment            | production, staging                 |
| status_code            | ok, error, rate_limited             |

---

## Derived KPIs

| KPI                          | Formula                                          |
|------------------------------|--------------------------------------------------|
| Success rate                 | (total - errors) / total x 100                  |
| Error rate by model          | errors.total grouped by gen_ai.request.model     |
| Average cost per request     | sum(cost) / count(requests)                      |
| Cost per successful request  | sum(cost) / count(successful requests)           |
| P95 latency by route         | histogram_quantile(0.95, latency) by route       |
| Token efficiency             | output_tokens / input_tokens                     |
| Retrieval yield              | useful retrieved docs / total retrieved docs     |

---

## Interoperability Rules

1. All signals MUST be emitted as standard OpenTelemetry traces, metrics, and logs.
2. Providers MAY add custom attributes but MUST NOT rename or redefine canonical fields.
3. Backends MAY transform label names for their storage format but MUST preserve canonical metric semantics.
4. The mandatory core (latency, tokens, cost, errors, retries, rate limits, trace coverage) MUST always be present.
5. Domain-specific quality signals (hallucination score, groundedness, relevance, task success) are OPTIONAL and placed in an extension pack.

---

## MVP Deliverables

- [ ] Python SDK with OTLP export
- [ ] TypeScript SDK with OTLP export
- [ ] Canonical metric names and tag definitions (this RFC)
- [ ] Default dashboards: latency, tokens, cost, errors
- [ ] Pluggable adapters: Prometheus, Grafana, Datadog, GCP Cloud Monitoring
- [ ] Example instrumentation for OpenAI, Anthropic, Vertex AI

---

## Open Questions

1. Should `gen_ai.cost_usd` be on spans or only on metrics?
2. How should multi-agent / chained traces be represented?
3. Should this align with the upstream OTEL GenAI semantic conventions working group?

---

## References

- OpenTelemetry Semantic Conventions: https://opentelemetry.io/docs/concepts/semantic-conventions/
- OTEL GenAI Working Group: https://github.com/open-telemetry/semantic-conventions/tree/main/docs/gen-ai
- OpenLLMetry: https://github.com/traceloop/openllmetry
