# open-llm-observability

> A vendor-neutral, OpenTelemetry-compatible semantic convention and SDK layer
> for standardizing LLM observability across any provider, framework, or platform.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![RFC Status: Draft v0.2](https://img.shields.io/badge/RFC-Draft%20v0.2-yellow)](RFC.md)
[![OTel Compatible](https://img.shields.io/badge/OpenTelemetry-compatible-blueviolet)](https://opentelemetry.io)

---

## The Problem

Every LLM observability tool today defines its own metric names, attribute schemas, and KPI calculations.

| Signal | OpenLLMetry | Langfuse | Arize Phoenix | This Proposal |
|---|---|---|---|---|
| Latency | `llm.request.duration` | `observation.latency` | `llm.latency_ms` | `gen_ai.client.operation.duration` |
| Input tokens | `llm.usage.prompt_tokens` | `usage.input` | `llm.token_count.prompt` | `gen_ai.usage.input_tokens` |
| Output tokens | `llm.usage.completion_tokens` | `usage.output` | `llm.token_count.completion` | `gen_ai.usage.output_tokens` |
| Cost | `llm.usage.total_cost` | `usage.totalCost` | *(proxy)* | `gen_ai.usage.cost` |

Teams that instrument once cannot portably observe everywhere. Switching backends means rewriting dashboards, alerts, and SLOs from scratch.

---

## The Solution

**One canonical schema. One SDK. Export everywhere.**

`open-llm-observability` defines:
- A universal set of **metric names, span attributes, and resource tags** for LLM workloads
- A lightweight **instrumentation SDK** (Python + TypeScript) that you add once
- **Pluggable exporters** to Prometheus, Grafana, Datadog, GCP, and any OTEL-compatible backend
- **Migration shims** from OpenLLMetry, Langfuse, Arize Phoenix, and AWS Bedrock

This project is designed to be upstreamed as a formal **OpenTelemetry `gen_ai.*` semantic convention extension**.

---

## Core Canonical Metrics

All compliant instrumentation libraries MUST emit these metrics:

| Metric | Instrument | Unit | Description |
|---|---|---|---|
| `gen_ai.client.operation.duration` | Histogram | `s` | End-to-end latency |
| `gen_ai.client.time_to_first_token` | Histogram | `s` | Streaming TTFT |
| `gen_ai.usage.input_tokens` | Counter | `{token}` | Prompt tokens |
| `gen_ai.usage.output_tokens` | Counter | `{token}` | Completion tokens |
| `gen_ai.usage.cost` | Counter | `usd` | Estimated cost |
| `gen_ai.client.error_rate` | Gauge | `1` | Rolling error ratio |
| `gen_ai.client.retry_count` | Counter | `{request}` | Retries |
| `gen_ai.client.rate_limit.events` | Counter | `{event}` | HTTP 429s |

See [RFC.md](RFC.md) for the full schema including span attributes, derived KPIs, resource attributes, and extension packs.

---

## Quick Start (Python)

```python
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider

meter = metrics.get_meter("gen_ai", version="1.0.0")
tracer = trace.get_tracer("gen_ai", tracer_version="1.0.0")

operation_duration = meter.create_histogram("gen_ai.client.operation.duration", unit="s")
input_tokens = meter.create_counter("gen_ai.usage.input_tokens", unit="{token}")
output_tokens = meter.create_counter("gen_ai.usage.output_tokens", unit="{token}")
cost = meter.create_counter("gen_ai.usage.cost", unit="usd")

# See examples/quickstart.py for full working example
```

---

## Extension Packs

Beyond the required core metrics, optional extension packs cover:

| Pack | Namespace | Coverage |
|---|---|---|
| RAG | `gen_ai.rag.*` | Retrieval latency, context recall, reranking |
| Agents | `gen_ai.agent.*` | Step counts, tool calls, agent duration |
| Eval | `gen_ai.eval.*` | Groundedness, faithfulness, relevance scores |
| Safety | `gen_ai.safety.*` | Content filtering and guardrail signals |
| Fine-tuning | `gen_ai.finetune.*` | Training run and fine-tune job signals |

---

## RFC

The full specification lives in [RFC.md](RFC.md) and covers:

1. Fragmentation problem with evidence
2. Prior art and OpenTelemetry precedent
3. Canonical metric schema (required)
4. Required span attributes
5. Derived KPIs and formulas
6. Extension packs
7. Migration guide from existing tools
8. Working SDK examples (Python + TypeScript)
9. Dashboard templates (PromQL / Grafana)
10. Real-world use cases
11. Upstream path to OpenTelemetry
12. Versioning and evolution policy
13. Open questions for the community

**[Read the RFC →](RFC.md)** | **[Join the Discussion →](https://github.com/sauravGit/open-llm-observability/discussions)**

---

## Project Structure

```
open-llm-observability/
├── RFC.md                    # Full specification (start here)
├── README.md
├── CONTRIBUTING.md
├── sdk/
│   └── python/               # Reference Python SDK
├── examples/
│   └── quickstart.py
├── dashboards/
│   └── grafana/              # gen_ai_core.json dashboard
└── .github/
    ├── workflows/ci.yml
    └── ISSUE_TEMPLATE/
```

---

## Status

| Component | Status |
|---|---|
| Core metric schema | Draft v0.2 |
| Required span attributes | Draft v0.2 |
| Python SDK | Scaffolded |
| TypeScript SDK | Planned |
| Migration shims | Draft |
| OTel SIG proposal | Planned |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). We especially welcome input from:
- SDK authors who have implemented LLM instrumentation
- Observability platform engineers at Langfuse, Arize, Traceloop, etc.
- OpenTelemetry SIG GenAI participants

Open questions and design decisions are tracked in [RFC.md § Open Questions](RFC.md#open-questions-for-the-community).

---

## License

Specification: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · Reference implementations: [Apache 2.0](LICENSE)
