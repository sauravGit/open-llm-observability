"""instrument.py - Main instrumentation entry point for open_llm_obs."""

from typing import Optional
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def instrument(
    provider: str,
    export_to: str = "otlp",
    endpoint: Optional[str] = None,
    service_name: Optional[str] = None,
    environment: str = "production",
) -> None:
    """Instrument your LLM application with canonical OTEL metrics and traces.

    Args:
        provider: LLM provider name (e.g. 'openai', 'anthropic', 'vertexai')
        export_to: Export destination ('otlp', 'prometheus', 'console')
        endpoint: OTLP collector endpoint (default: localhost:4317)
        service_name: Service name for OTEL resource attributes
        environment: Deployment environment (default: 'production')

    Example:
        from open_llm_obs import instrument
        instrument(provider='openai', export_to='otlp')
    """
    _endpoint = endpoint or "http://localhost:4317"
    _service_name = service_name or f"{provider}-service"

    # Set up Tracer Provider
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=_endpoint))
    )
    trace.set_tracer_provider(tracer_provider)

    # Set up Meter Provider
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=_endpoint)
    )
    meter_provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)

    print(f"[open-llm-observability] Instrumented provider={provider}, "
          f"export_to={export_to}, endpoint={_endpoint}")
