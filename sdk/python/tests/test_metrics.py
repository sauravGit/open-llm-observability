"""Unit tests for open_llm_obs.metrics (LLMMetrics) — RFC-0001 v0.2."""
import pytest
from unittest.mock import MagicMock, patch
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader


class TestLLMMetrics:
    """Tests for the LLMMetrics canonical metric recorder."""

    def _make_metrics(self):
        """Return an LLMMetrics instance backed by an InMemoryMetricReader."""
        self.reader = InMemoryMetricReader()
        provider = MeterProvider(metric_readers=[self.reader])

        # Patch the module-level meter to use our test provider
        with patch("open_llm_obs.metrics._meter", provider.get_meter("open_llm_obs", version="0.2.0")):
            from open_llm_obs.metrics import LLMMetrics
            return LLMMetrics(provider="openai", model="gpt-4o")

    # ------------------------------------------------------------------
    # Instantiation
    # ------------------------------------------------------------------

    def test_instantiation(self):
        """LLMMetrics should instantiate without raising."""
        from open_llm_obs.metrics import LLMMetrics
        m = LLMMetrics(provider="openai", model="gpt-4o")
        assert m.provider == "openai"
        assert m.model == "gpt-4o"

    def test_all_core_instruments_created(self):
        """All 8 required RFC-0001 core instruments should be present."""
        from open_llm_obs.metrics import LLMMetrics
        m = LLMMetrics(provider="openai", model="gpt-4o")
        assert hasattr(m, "operation_duration")
        assert hasattr(m, "time_to_first_token")
        assert hasattr(m, "input_tokens")
        assert hasattr(m, "output_tokens")
        assert hasattr(m, "cost")
        assert hasattr(m, "error_rate")
        assert hasattr(m, "retry_count")
        assert hasattr(m, "rate_limit_events")

    # ------------------------------------------------------------------
    # record_request — happy path
    # ------------------------------------------------------------------

    def test_record_request_success(self):
        """record_request() should not raise for a valid successful call."""
        from open_llm_obs.metrics import LLMMetrics
        m = LLMMetrics(provider="openai", model="gpt-4o")
        m.record_request(
            duration_s=0.42,
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.002,
            error=False,
        )

    def test_record_request_with_ttft(self):
        """record_request() with time_to_first_token_s should not raise."""
        from open_llm_obs.metrics import LLMMetrics
        m = LLMMetrics(provider="anthropic", model="claude-3-opus")
        m.record_request(
            duration_s=1.2,
            input_tokens=200,
            output_tokens=80,
            cost_usd=0.005,
            time_to_first_token_s=0.15,
        )

    def test_record_request_error(self):
        """record_request() with error=True should not raise."""
        from open_llm_obs.metrics import LLMMetrics
        m = LLMMetrics(provider="openai", model="gpt-4o")
        m.record_request(
            duration_s=0.1,
            input_tokens=10,
            output_tokens=0,
            cost_usd=0.0,
            error=True,
        )

    def test_record_request_custom_operation(self):
        """record_request() should accept a custom operation name."""
        from open_llm_obs.metrics import LLMMetrics
        m = LLMMetrics(provider="openai", model="gpt-4o")
        m.record_request(
            duration_s=0.5,
            input_tokens=50,
            output_tokens=30,
            cost_usd=0.001,
            operation="embed",
        )

    # ------------------------------------------------------------------
    # _base_attrs — required RFC-0001 span attributes
    # ------------------------------------------------------------------

    def test_base_attrs_contains_required_keys(self):
        """_base_attrs() must return gen_ai.system, gen_ai.request.model, gen_ai.operation.name."""
        from open_llm_obs.metrics import LLMMetrics
        m = LLMMetrics(provider="openai", model="gpt-4o")
        attrs = m._base_attrs()
        assert attrs["gen_ai.system"] == "openai"
        assert attrs["gen_ai.request.model"] == "gpt-4o"
        assert attrs["gen_ai.operation.name"] == "chat"

    def test_base_attrs_custom_operation(self):
        """_base_attrs() should use the provided operation name."""
        from open_llm_obs.metrics import LLMMetrics
        m = LLMMetrics(provider="openai", model="gpt-4o")
        attrs = m._base_attrs(operation="embed")
        assert attrs["gen_ai.operation.name"] == "embed"

    # ------------------------------------------------------------------
    # Metric name validation — ensure RFC-0001 canonical names are used
    # ------------------------------------------------------------------

    def test_canonical_metric_names(self):
        """Instrument names must match RFC-0001 canonical gen_ai.* names exactly."""
        from open_llm_obs.metrics import LLMMetrics
        m = LLMMetrics(provider="openai", model="gpt-4o")
        # Verify instrument names via their _name attribute (OTel SDK)
        assert m.operation_duration._name == "gen_ai.client.operation.duration"
        assert m.time_to_first_token._name == "gen_ai.client.time_to_first_token"
        assert m.input_tokens._name == "gen_ai.usage.input_tokens"
        assert m.output_tokens._name == "gen_ai.usage.output_tokens"
        assert m.cost._name == "gen_ai.usage.cost"
        assert m.retry_count._name == "gen_ai.client.retry_count"
        assert m.rate_limit_events._name == "gen_ai.client.rate_limit.events"
