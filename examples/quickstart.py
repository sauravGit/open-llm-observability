"""Quickstart: Instrument an OpenAI call with open-llm-observability (RFC-0001 v0.2).

This example shows how to use the LLMMetrics SDK to capture all RFC-0001 required
canonical gen_ai.* metrics from a single OpenAI chat completion call, exported via OTLP.

Metrics emitted:
    gen_ai.client.operation.duration  Histogram  s
    gen_ai.client.time_to_first_token Histogram  s      (streaming only — simulated here)
    gen_ai.usage.input_tokens         Counter    {token}
    gen_ai.usage.output_tokens        Counter    {token}
    gen_ai.usage.cost                 Counter    usd
    gen_ai.client.retry_count         Counter    {request}  (only on error)

Span attributes emitted (RFC-0001 required):
    gen_ai.system, gen_ai.request.model, gen_ai.operation.name,
    gen_ai.response.model, gen_ai.usage.input_tokens, gen_ai.usage.output_tokens

Prerequisites:
    pip install open-llm-obs openai opentelemetry-exporter-otlp-proto-grpc

Run:
    # Start a local OTLP collector (e.g. Grafana Alloy or otel-collector)
    python examples/quickstart.py
"""
import os
import time

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

from open_llm_obs.metrics import LLMMetrics

# ---------------------------------------------------------------------------
# 1. Set up OpenTelemetry SDK (console exporters for local dev)
# ---------------------------------------------------------------------------

tracer_provider = TracerProvider()
tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(tracer_provider)

reader = PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=5000)
meter_provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(meter_provider)

tracer = trace.get_tracer("gen_ai", tracer_version="1.0.0")

# ---------------------------------------------------------------------------
# 2. Initialise LLMMetrics for this provider + model pair
# ---------------------------------------------------------------------------

llm_metrics = LLMMetrics(provider="openai", model="gpt-4o")

# ---------------------------------------------------------------------------
# 3. Make an instrumented LLM call
# ---------------------------------------------------------------------------

def call_openai(prompt: str) -> str:
    """Call the OpenAI chat completion API and record RFC-0001 canonical metrics."""
    import openai

    span_attrs = {
        "gen_ai.system": "openai",
        "gen_ai.request.model": "gpt-4o",
        "gen_ai.operation.name": "chat",
    }

    with tracer.start_as_current_span("gen_ai.chat", attributes=span_attrs) as span:
        t0 = time.perf_counter()
        error = False
        ttft = None

        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
            )
            duration_s = time.perf_counter() - t0

            in_tok = response.usage.prompt_tokens
            out_tok = response.usage.completion_tokens
            # Estimate cost: $3/M input, $15/M output (gpt-4o pricing)
            cost_usd = (in_tok * 0.000003) + (out_tok * 0.000015)

            # Enrich span with RFC-0001 required response attributes
            span.set_attribute("gen_ai.response.model", response.model)
            span.set_attribute("gen_ai.usage.input_tokens", in_tok)
            span.set_attribute("gen_ai.usage.output_tokens", out_tok)

            content = response.choices[0].message.content

        except Exception as exc:
            duration_s = time.perf_counter() - t0
            in_tok = 0
            out_tok = 0
            cost_usd = 0.0
            error = True
            span.record_exception(exc)
            raise

        finally:
            # Record all RFC-0001 required core metrics
            llm_metrics.record_request(
                duration_s=duration_s,
                input_tokens=in_tok,
                output_tokens=out_tok,
                cost_usd=cost_usd,
                error=error,
                time_to_first_token_s=ttft,
            )

        return content


# ---------------------------------------------------------------------------
# 4. Simulated run (no real API key needed for metric emission demo)
# ---------------------------------------------------------------------------

def simulated_response() -> None:
    """Record metrics using simulated values — no OpenAI API key required."""
    print("[open-llm-observability quickstart] Recording simulated RFC-0001 metrics...")

    llm_metrics.record_request(
        duration_s=0.83,
        input_tokens=142,
        output_tokens=67,
        cost_usd=(142 * 0.000003) + (67 * 0.000015),
        error=False,
        time_to_first_token_s=0.12,
        operation="chat",
    )

    print("[open-llm-observability quickstart] Metrics recorded:")
    print("  gen_ai.client.operation.duration  = 0.83 s")
    print("  gen_ai.client.time_to_first_token = 0.12 s")
    print("  gen_ai.usage.input_tokens         = 142 {token}")
    print("  gen_ai.usage.output_tokens        = 67  {token}")
    print(f"  gen_ai.usage.cost                 = {(142 * 0.000003) + (67 * 0.000015):.6f} usd")
    print("\nWaiting for metric export (5s)...")
    time.sleep(6)
    print("Done. Check your collector / console output above.")


if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        result = call_openai("What is OpenTelemetry in one sentence?")
        print(f"Response: {result}")
        time.sleep(6)  # wait for metric flush
    else:
        print("OPENAI_API_KEY not set — running in simulation mode.")
        simulated_response()
