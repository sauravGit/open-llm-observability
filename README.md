# open-llm-observability

> A vendor-neutral, OpenTelemetry-compatible semantic convention and SDK layer
> for standardizing LLM observability across any provider, framework, or platform.

---

## The Problem

Every LLM platform emits observability data differently.  
Tokens are named differently. Latency is measured differently. Cost is tracked differently — or not at all.  
Developers re-instrument for every new backend.

## The Solution

**One canonical schema. One SDK. Export everywhere.**

`open-llm-observability` defines:
- A universal set of **metric names, span attributes, and resource tags** for LLM workloads
- A lightweight **instrumentation SDK** (Python + TypeScript) that you add once
- **Pluggable exporters** to Prometheus, Grafana, Datadog, GCP, and any OTEL-compatible backend

---

## Canonical Metric Names (excerpt)

| Metric                        | Type      | Description                    |
|-------------------------------|-----------|--------------------------------|
| gen_ai.requests.total         | Counter   | Total inference requests       |
| gen_ai.latency                | Histogram | End-to-end latency (ms)        |
| gen_ai.time_to_first_token    | Histogram | Streaming first-token latency  |
| gen_ai.usage.total_tokens     | Histogram | Total tokens consumed          |
| gen_ai.usage.cost             | Histogram | Estimated USD cost             |
| gen_ai.requests.errors.total  | Counter   | Failed requests                |

Full schema: [RFC.md](./RFC.md)

---

## Quick Start (Python)

```python
from open_llm_obs import instrument

instrument(provider="openai", export_to="otlp")

# Your existing OpenAI calls are now fully instrumented
```

---

## Architecture

```
Your LLM App
    └── open-llm-observability SDK
            ├── Canonical metric names & span attributes (RFC.md)
            ├── OTLP exporter (traces + metrics + logs)
            └── Pluggable adapters
                    ├── Prometheus
                    ├── Grafana
                    ├── Datadog
                    └── GCP Cloud Monitoring
```

---

## Semantic Convention (summary)

### Resource Attributes
- `service.name`, `service.version`, `deployment.environment`
- `gen_ai.provider`, `gen_ai.model`, `gen_ai.app.name`, `gen_ai.region`

### Span Names
- `gen_ai.request`, `gen_ai.stream`, `gen_ai.tool_call`, `gen_ai.retrieval`, `gen_ai.guardrail`, `gen_ai.embedding`

### Derived KPIs
- Success rate, error rate by model, average cost per request, P95 latency by route, token efficiency, retrieval yield

See [RFC.md](./RFC.md) for the full specification.

---

## Status

- [x] RFC v0.1 draft
- [ ] Python SDK (in progress)
- [ ] TypeScript SDK
- [ ] Adapters: Prometheus, Grafana, Datadog, GCP
- [ ] Default dashboards

---

## Contributing

This project is in active RFC phase. Open a [Discussion](../../discussions) to provide feedback on:
- Metric naming conventions
- Scope of the mandatory core vs. optional domain extension packs
- OTEL semantic convention mapping
- Backend adapter priorities

---

## License

Apache 2.0 — see [LICENSE](./LICENSE)
