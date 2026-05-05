"""Quickstart: Instrument an OpenAI call with open-llm-observability.

This example shows how to use the SDK to capture gen_ai.* canonical
metrics from a single OpenAI chat completion call using the OTLP exporter.

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

from open_llm_obs.instrument import instrument
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

# ---------------------------------------------------------------------------
# 2. Instrument (auto-patches openai if installed)
# ---------------------------------------------------------------------------

instrument(provider="openai")

# ---------------------------------------------------------------------------
# 3. Simulate an LLM call and record canonical gen_ai.* metrics manually
#    (the auto-instrumentation does this for you when openai is installed)
# ---------------------------------------------------------------------------

llm_metrics = LLMMetrics(meter_provider=meter_provider)

start = time.time()

# Simulate a completion (replace with a real openai call in production)
simulated_response = {
    "model": "gpt-4o",
    "usage": {"prompt_tokens": 120, "completion_tokens": 80},
    "latency_ms": 320,
}

llm_metrics.record(
    model=simulated_response["model"],
    provider="openai",
    input_tokens=simulated_response["usage"]["prompt_tokens"],
    output_tokens=simulated_response["usage"]["completion_tokens"],
    duration_ms=simulated_response["latency_ms"],
    error=False,
)

print(
    f"Recorded metrics for model={simulated_response['model']} "
    f"input_tokens={simulated_response['usage']['prompt_tokens']} "
    f"output_tokens={simulated_response['usage']['completion_tokens']} "
    f"duration_ms={simulated_response['latency_ms']}"
)

time.sleep(6)  # wait for the metric reader to flush
print("Done. Check your OTLP collector or console output for gen_ai.* metrics.")
