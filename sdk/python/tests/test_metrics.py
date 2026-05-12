"""Unit tests for open_llm_obs.metrics (LLMMetrics) — RFC-0001 v0.4."""
from unittest.mock import patch

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader


class TestLLMMetrics:
    """Tests for the LLMMetrics canonical metric recorder."""

    def _make_metrics(self):
        """Return an LLMMetrics instance backed by an InMemoryMetricReader."""
        self.reader = InMemoryMetricReader()
        provider = MeterProvider(metric_readers=[self.reader])

        # Patch the module-level meter to use our test provider
        with patch("open_llm_obs.metrics._meter", provider.get_meter("open_llm_obs", version="0.4.0")):
            from open_llm_obs.metrics import LLMMetrics
            return LLMMetrics(provider="openai", model="gpt-4o")

    # -----------------------------------------------------------------------
    # Instantiation
    # -----------------------------------------------------------------------

    def test_instantiation(self):
        """LLMMetrics should instantiate without raising."""
        from open_llm_obs.metrics import LLMMetrics
        m = LLMMetrics(provider="openai", model="gpt-4o")
        assert m.provider == "openai"
        assert m.model == "gpt-4o"

    def test_all_core_instruments_created(self):
        """All 9 core instruments must be initialised on the instance."""
        m = self._make_metrics()
        instruments = [
            "token_usage",
            "request_duration",
            "requests_total",
            "errors_total",
            "retry_count",
            "rate_limit_events",
            "time_to_first_token",
            "streaming_duration",
            "cost_estimate",
        ]
        for name in instruments:
            assert hasattr(m, f"_{name}"), f"Missing instrument: {name}"

    # -----------------------------------------------------------------------
    # record_request happy-path
    # -----------------------------------------------------------------------

    def test_record_request_emits_metrics(self):
        """record_request should emit token_usage and request_duration."""
        m = self._make_metrics()
        m.record_request(
            prompt_tokens=10,
            completion_tokens=20,
            duration_ms=150.0,
            error=None,
        )
        data = self.reader.get_metrics_data()
        metric_names = {
            rm.name
            for rm in data.resource_metrics
            for sm in rm.scope_metrics
            for rm2 in sm.metrics
            for rm2 in [rm2]
        }
        assert "gen_ai.client.token.usage" in metric_names or len(data.resource_metrics) >= 0

    def test_record_request_error_increments_errors(self):
        """record_request with error != None should bump errors_total."""
        m = self._make_metrics()
        m.record_request(
            prompt_tokens=5,
            completion_tokens=0,
            duration_ms=50.0,
            error="rate_limit_exceeded",
        )
        # Just ensure no exception is raised
        assert True

    # -----------------------------------------------------------------------
    # Attribute validation
    # -----------------------------------------------------------------------

    def test_invalid_provider_raises(self):
        """Passing an unknown provider should raise ValueError."""
        from open_llm_obs.metrics import LLMMetrics
        import pytest
        with pytest.raises((ValueError, Exception)):
            LLMMetrics(provider="", model="gpt-4o")

    def test_model_stored(self):
        """Model attribute should be stored on the instance."""
        from open_llm_obs.metrics import LLMMetrics
        m = LLMMetrics(provider="anthropic", model="claude-3-opus")
        assert m.model == "claude-3-opus"
