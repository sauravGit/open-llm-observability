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
        """All core instruments must be initialised on the instance."""
        m = self._make_metrics()
        instruments = [
            "operation_duration",
            "time_to_first_token",
            "input_tokens",
            "output_tokens",
            "cost",
            "error_rate",
            "retry_count",
            "rate_limit_events",
        ]
        for name in instruments:
            assert hasattr(m, f"_{name}"), f"Missing instrument: {name}"

    # -----------------------------------------------------------------------
    # record_request happy-path
    # -----------------------------------------------------------------------

    def test_record_request_no_error(self):
        """record_request should not raise when called with valid args."""
        m = self._make_metrics()
        m.record_request(
            duration_s=0.15,
            input_tokens=10,
            output_tokens=20,
            cost_usd=0.001,
        )

    def test_record_request_with_error(self):
        """record_request with error=True should not raise."""
        m = self._make_metrics()
        m.record_request(
            duration_s=0.05,
            input_tokens=5,
            output_tokens=0,
            cost_usd=0.0,
            error=True,
        )

    def test_record_request_with_streaming(self):
        """record_request with time_to_first_token_s should not raise."""
        m = self._make_metrics()
        m.record_request(
            duration_s=1.2,
            input_tokens=50,
            output_tokens=200,
            cost_usd=0.01,
            time_to_first_token_s=0.3,
        )

    # -----------------------------------------------------------------------
    # Attribute validation
    # -----------------------------------------------------------------------

    def test_model_stored(self):
        """Model attribute should be stored on the instance."""
        from open_llm_obs.metrics import LLMMetrics
        m = LLMMetrics(provider="anthropic", model="claude-3-opus")
        assert m.model == "claude-3-opus"

    def test_provider_stored(self):
        """Provider attribute should be stored on the instance."""
        from open_llm_obs.metrics import LLMMetrics
        m = LLMMetrics(provider="google", model="gemini-pro")
        assert m.provider == "google"
