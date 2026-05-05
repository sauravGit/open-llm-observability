"""metrics.py - Canonical LLM metric definitions per RFC-0001."""

from opentelemetry import metrics

_meter = metrics.get_meter("open_llm_obs", version="0.1.0")


class LLMMetrics:
    """Canonical LLM metrics as defined in RFC-0001.

    All metric names follow the gen_ai.* namespace convention.
    """

    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model

        # Counters
        self.requests_total = _meter.create_counter(
            name="gen_ai.requests.total",
            description="Total number of LLM inference requests",
            unit="{req}",
        )
        self.requests_errors_total = _meter.create_counter(
            name="gen_ai.requests.errors.total",
            description="Total number of failed LLM inference requests",
            unit="{req}",
        )
        self.tool_calls_total = _meter.create_counter(
            name="gen_ai.tool_calls.total",
            description="Total number of tool/function calls",
            unit="{call}",
        )
        self.guardrail_violations_total = _meter.create_counter(
            name="gen_ai.guardrail.violations.total",
            description="Total number of safety/policy violations",
            unit="{viol}",
        )

        # Histograms
        self.latency = _meter.create_histogram(
            name="gen_ai.latency",
            description="End-to-end request latency in milliseconds",
            unit="ms",
        )
        self.time_to_first_token = _meter.create_histogram(
            name="gen_ai.time_to_first_token",
            description="Time to first streaming token in milliseconds",
            unit="ms",
        )
        self.input_tokens = _meter.create_histogram(
            name="gen_ai.usage.input_tokens",
            description="Input token count per request",
            unit="{tok}",
        )
        self.output_tokens = _meter.create_histogram(
            name="gen_ai.usage.output_tokens",
            description="Output token count per request",
            unit="{tok}",
        )
        self.total_tokens = _meter.create_histogram(
            name="gen_ai.usage.total_tokens",
            description="Total token count per request",
            unit="{tok}",
        )
        self.cost = _meter.create_histogram(
            name="gen_ai.usage.cost",
            description="Estimated USD cost per request",
            unit="USD",
        )
        self.retrieval_docs = _meter.create_histogram(
            name="gen_ai.retrieval.docs_returned",
            description="Number of documents returned per retrieval step",
            unit="{doc}",
        )

    def _base_attrs(self, **kwargs) -> dict:
        """Return base attributes for all metrics."""
        return {
            "gen_ai.system": self.provider,
            "gen_ai.request.model": self.model,
            **kwargs,
        }

    def record_request(
        self,
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        status: str = "ok",
        route: str = "/",
        request_type: str = "chat",
    ) -> None:
        """Record metrics for a completed LLM request."""
        attrs = self._base_attrs(
            status_code=status,
            "gen_ai.request.route"=route,
            "gen_ai.request.type"=request_type,
        )
        total = input_tokens + output_tokens

        self.requests_total.add(1, attrs)
        if status != "ok":
            self.requests_errors_total.add(1, attrs)

        self.latency.record(latency_ms, attrs)
        self.input_tokens.record(input_tokens, attrs)
        self.output_tokens.record(output_tokens, attrs)
        self.total_tokens.record(total, attrs)
        self.cost.record(cost_usd, attrs)
