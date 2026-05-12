# open-llm-observability

> A vendor-neutral, OpenTelemetry-compatible semantic convention and SDK layer for standardizing LLM observability across any provider, framework, or platform.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![RFC Status: Draft v0.4](https://img.shields.io/badge/RFC-Draft%20v0.4-yellow)](RFC.md)
[![OTel Compatible](https://img.shields.io/badge/OpenTelemetry-compatible-blueviolet)](https://opentelemetry.io)
[![GitHub stars](https://img.shields.io/github/stars/sauravGit/open-llm-observability)](https://github.com/sauravGit/open-llm-observability/stargazers)

---

## The Problem

Every LLM observability tool today defines its own metric names, attribute schemas, and KPI calculations.

| Signal | OpenLLMetry | Langfuse | OpenInference | Arize Phoenix | AWS Bedrock | **Canonical** |
|--------|-------------|----------|---------------|---------------|-------------|---------------|
| Latency | `llm.request.duration` | `observation.latency` | `llm.latency` | `llm.latency_ms` | `TotalInferenceTime` | `gen_ai.client.operation.duration` |
| Input tokens | `llm.usage.prompt_tokens` | `usage.input` | `llm.token_count.prompt` | `llm.token_count.prompt` | `InputTokenCount` | `gen_ai.usage.input_tokens` |
| Output tokens | `llm.usage.completion_tokens` | `usage.output` | `llm.token_count.completion` | `llm.token_count.completion` | `OutputTokenCount` | `gen_ai.usage.output_tokens` |
| Cost | `llm.usage.total_cost` | `usage.totalCost` | `llm.cost.total` | (proxy) | CloudWatch | `gen_ai.usage.cost` |
| TTFT | (none) | (none) | (none) | (none) | `TimeToFirstByte` | `gen_ai.client.time_to_first_token` |

Teams that instrument once cannot portably observe everywhere. Switching backends means rewriting dashboards, alerts, and SLOs from scratch.

---

## The Solution

**One canonical schema. One SDK. Export everywhere.**

`open-llm-observability` defines:

- **A universal metric schema** — canonical `gen_ai.*` names for latency, tokens, cost, errors, retries, rate limits
- **A lightweight Python SDK** — drop-in instrumentation that you add once
- **Pluggable exporters** — to Prometheus, Grafana, Datadog, GCP, and any OTel-compatible backend
- **Migration shims** — normalize from OpenLLMetry, Langfuse, OpenInference, Arize Phoenix, and AWS Bedrock
- **Extension packs** — RAG, Agents, Eval, and Safety observability
- **Dashboard templates** — ready-to-use Grafana dashboards with alert rules

---

## Core Canonical Metrics

| Metric | Instrument | Unit | Description |
|--------|------------|------|-------------|
| `gen_ai.client.operation.duration` | Histogram | `s` | End-to-end request latency |
| `gen_ai.client.time_to_first_token` | Histogram | `s` | Streaming TTFT |
| `gen_ai.usage.input_tokens` | Counter | `{token}` | Prompt tokens |
| `gen_ai.usage.output_tokens` | Counter | `{token}` | Completion tokens |
| `gen_ai.usage.total_tokens` | Counter | `{token}` | Total tokens |
| `gen_ai.client.error_count` | Counter | `{error}` | Per-request errors |
| `gen_ai.client.retry_count` | Counter | `{retry}` | Retry attempts |
| `gen_ai.client.rate_limit.events` | Counter | `{event}` | HTTP 429 / throttling |

## Quick Start (Python)

```python
from open_llm_obs import LLMTracer, LLMetrics

tracer = LLMTracer(service_name="my-llm-app")
metrics = LLMetrics()

with tracer.trace_llm(operation="chat", model="gpt-4", system="openai") as span:
    span.set_prompt(messages)
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=500
    )
    
    span.set_completion(
        content=response.choices[0].message.content,
        finish_reason=response.choices[0].finish_reason
    )
    
    metrics.record_tokens(
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        total_tokens=response.usage.total_tokens
    )
```

See [`examples/quickstart.py`](examples/quickstart.py) for the full working example.

---

## Extension Packs

| Pack | Namespace | Coverage |
|------|-----------|----------|
| **Cost** | `gen_ai.usage.cost` | Estimated request cost in microdollars |
| **RAG** | `gen_ai.rag.*` | Retrieval latency, document counts, reranking |
| **Agents** | `gen_ai.agent.*` | Step counts, tool calls, agent duration |
| **Eval** | `gen_ai.eval.*` | Groundedness, faithfulness, relevance |
| **Safety** | `gen_ai.safety.*` | Content filtering and guardrails |

---

## Migration

This project provides normalization shims to map from existing schemas to canonical `gen_ai.*` names:

- [OpenLLMetry](RFC.md#91-openllmetry-to-canonical)
- [Langfuse](RFC.md#92-langfuse-to-canonical)
- [OpenInference](RFC.md#93-openinference-to-canonical)
- [Arize Phoenix](RFC.md#94-arize-phoenix-to-canonical)
- [AWS Bedrock](RFC.md#95-aws-bedrock-to-canonical)

---

## Project Structure

```
open-llm-observability/
├── RFC.md              # Full specification (start here)
├── README.md           # This file
├── CONTRIBUTING.md     # How to contribute
├── LICENSE             # Apache 2.0
├── sdk/
│   └── python/         # Reference Python SDK (open_llm_obs)
├── examples/
│   └── quickstart.py   # Working Python example
├── dashboards/
│   └── grafana/        # Grafana dashboard templates
└── .github/
    └── workflows/ci.yml
```

---

## Status

| Component | Status | Version |
|-----------|--------|--------|
| Core metric schema | Draft | v0.4 |
| Required span attributes | Draft | v0.4 |
| Python SDK | Scaffolded | 0.4.0 |
| TypeScript SDK | Planned | - |
| Migration shims | Draft | v0.4 |
| OTel SIG proposal | Filed | Issue #101 |

**Upstream:** [OTel GenAI #101](https://github.com/open-telemetry/semantic-conventions-genai/issues/101)  
**Discussion:** [RFC Discussion #1](https://github.com/sauravGit/open-llm-observability/discussions/1)

---

## Contributing

This is a community-driven project. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get involved.

1. **Use the spec** in your LLM app and share feedback
2. **Open issues** for gaps in the schema
3. **Submit PRs** for migration shims, SDK improvements, or dashboard templates
4. **Engage with OTel GenAI** on Issue #101

---

## License

Specification: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)  
Reference implementations: [Apache 2.0](LICENSE)
