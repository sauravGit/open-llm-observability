"""Unit tests for open_llm_obs.metrics (LLMMetrics)."""

import pytest
from unittest.mock import MagicMock, patch


class TestLLMMetrics:
    """Tests for the LLMMetrics canonical metric recorder."""

    def _make_metrics(self):
        """Return an LLMMetrics instance backed by a no-op MeterProvider."""
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import InMemoryMetricReader

        self.reader = InMemoryMetricReader()
        provider = MeterProvider(metric_readers=[self.reader])

        from open_llm_obs.metrics import LLMMetrics

        return LLMMetrics(meter_provider=provider)

    def test_record_success(self):
        """record() should not raise for a valid successful call."""
        m = self._make_metrics()
        m.record(
            model="gpt-4o",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
            duration_ms=200,
            error=False,
        )

    def test_record_error(self):
        """record() should not raise when error=True."""
        m = self._make_metrics()
        m.record(
            model="claude-3-opus",
            provider="anthropic",
            input_tokens=80,
            output_tokens=0,
            duration_ms=150,
            error=True,
        )

    def test_record_emits_token_metrics(self):
        """record() should emit gen_ai.usage.input_tokens and gen_ai.usage.output_tokens."""
        m = self._make_metrics()
        m.record(
            model="gemini-1.5-pro",
            provider="google",
            input_tokens=200,
            output_tokens=100,
            duration_ms=300,
            error=False,
        )
        metrics_data = self.reader.get_metrics_data()
        metric_names = {
            metric.name
            for resource_metric in metrics_data.resource_metrics
            for scope_metric in resource_metric.scope_metrics
            for metric in scope_metric.metrics
        }
        assert "gen_ai.usage.input_tokens" in metric_names
        assert "gen_ai.usage.output_tokens" in metric_names

    def test_record_emits_duration_metric(self):
        """record() should emit gen_ai.client.operation.duration."""
        m = self._make_metrics()
        m.record(
            model="gpt-4o-mini",
            provider="openai",
            input_tokens=50,
            output_tokens=25,
            duration_ms=100,
            error=False,
        )
        metrics_data = self.reader.get_metrics_data()
        metric_names = {
            metric.name
            for resource_metric in metrics_data.resource_metrics
            for scope_metric in resource_metric.scope_metrics
            for metric in scope_metric.metrics
        }
        assert "gen_ai.client.operation.duration" in metric_names
