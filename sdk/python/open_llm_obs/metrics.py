"""metrics.py - Canonical LLM metric definitions per RFC-0001 v0.4.

All metric names, instruments, and units follow the gen_ai.* namespace
as defined in RFC-0001: LLM Observability Semantic Conventions for OpenTelemetry.

RFC: https://github.com/sauravGit/open-llm-observability/blob/main/RFC.md
"""
from __future__ import annotations

from typing import Optional
from opentelemetry import metrics

_meter = metrics.get_meter("open_llm_obs", version="0.4.0")


class LLMMetrics:
    """Canonical LLM metrics as defined in RFC-0001 v0.4.

    All metric names follow the gen_ai.* namespace convention.
    Instruments and units match the RFC-0001 Core Metrics schema exactly.

    Required core metrics (MUST be emitted by compliant instrumentation):
      gen_ai.client.operation.duration  Histogram  s
      gen_ai.client.time_to_first_token Histogram  s
      gen_ai.usage.input_tokens         Counter    {token}
      gen_ai.usage.output_tokens        Counter    {token}
      gen_ai.usage.cost                 Counter    usd
      gen_ai.client.error_rate          Gauge      1
      gen_ai.client.retry_count         Counter    {request}
      gen_ai.client.rate_limit.events   Counter    {event}
    """

    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model

        # -----------------------------------------------------------------------
        # Core metrics — REQUIRED (RFC-0001 §Canonical Metric Schema)
        # -----------------------------------------------------------------------

        # End-to-end latency from request sent to last response byte received
        self.operation_duration = _meter.create_histogram(
            name="gen_ai.client.operation.duration",
            description="End-to-end latency from request sent to last response byte received",
            unit="s",
        )

        # Time from request sent to first response token (streaming only)
        self.time_to_first_token = _meter.create_histogram(
            name="gen_ai.client.time_to_first_token",
            description="Time from request sent to first response token (streaming only)",
            unit="s",
        )

        # Number of tokens in the input/prompt
        self.input_tokens = _meter.create_counter(
            name="gen_ai.usage.input_tokens",
            description="Number of tokens in the input/prompt",
            unit="{token}",
        )

        # Number of tokens in the model response
        self.output_tokens = _meter.create_counter(
            name="gen_ai.usage.output_tokens",
            description="Number of tokens in the model response",
            unit="{token}",
        )

        # Estimated cost of the request in USD
        self.cost = _meter.create_counter(
            name="gen_ai.usage.cost",
            description="Estimated cost of the request in USD",
            unit="usd",
        )

        # Ratio of failed requests to total requests (rolling 1-min window)
        self.error_rate = _meter.create_gauge(
            name="gen_ai.client.error_rate",
            description="Ratio of failed requests to total requests (rolling 1-min window)",
            unit="1",
        )

        # Number of retry attempts made for throttled or failed requests
        self.retry_count = _meter.create_counter(
            name="gen_ai.client.retry_count",
            description="Number of retry attempts made for throttled or failed requests",
            unit="{request}",
        )

        # Number of rate limit responses (HTTP 429) received from the provider
        self.rate_limit_events = _meter.create_counter(
            name="gen_ai.client.rate_limit.events",
            description="Number of rate limit responses (HTTP 429) received from the provider",
            unit="{event}",
        )

    def _base_attrs(self, operation: str = "chat") -> dict:
        """Base span/metric attributes required by RFC-0001."""
        return {
            "gen_ai.system": self.provider,
            "gen_ai.request.model": self.model,
            "gen_ai.operation.name": operation,
        }

    def record_request(
        self,
        *,
        duration_s: float,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        error: bool = False,
        time_to_first_token_s: Optional[float] = None,
        operation: str = "chat",
    ) -> None:
        """Record all core metrics for a single LLM request.

        Args:
            duration_s: End-to-end wall-clock duration in seconds.
            input_tokens: Number of prompt/input tokens.
            output_tokens: Number of completion/output tokens.
            cost_usd: Estimated cost in USD.
            error: Whether the request resulted in an error.
            time_to_first_token_s: Seconds to first token (streaming only).
            operation: gen_ai.operation.name value (default: 'chat').
        """
        attrs = self._base_attrs(operation)

        self.operation_duration.record(duration_s, attrs)
        self.input_tokens.add(input_tokens, attrs)
        self.output_tokens.add(output_tokens, attrs)
        self.cost.add(cost_usd, attrs)

        if time_to_first_token_s is not None:
            self.time_to_first_token.record(time_to_first_token_s, attrs)

        if error:
            self.retry_count.add(1, attrs)
