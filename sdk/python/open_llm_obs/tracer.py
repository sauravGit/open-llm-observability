"""tracer.py - LLM span tracer using OpenTelemetry per RFC-0001 span conventions."""

import time
from contextlib import contextmanager
from typing import Optional, Generator
from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode


class LLMTracer:
    """Creates OpenTelemetry spans for LLM operations per RFC-0001 span naming."""

    def __init__(self, provider: str, model: str, app_name: str = "llm-app"):
        self.provider = provider
        self.model = model
        self.app_name = app_name
        self._tracer = trace.get_tracer("open_llm_obs", "0.1.0")

    def _base_attrs(self, **kwargs) -> dict:
        return {
            "gen_ai.system": self.provider,
            "gen_ai.request.model": self.model,
            "gen_ai.app.name": self.app_name,
            **kwargs,
        }

    @contextmanager
    def request(
        self,
        request_type: str = "chat",
        route: str = "/",
    ) -> Generator[Span, None, None]:
        """Context manager for a gen_ai.request span."""
        attrs = self._base_attrs(
            **{
                "gen_ai.request.type": request_type,
                "gen_ai.request.route": route,
            }
        )
        with self._tracer.start_as_current_span(
            "gen_ai.request", attributes=attrs
        ) as span:
            start = time.perf_counter()
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as exc:
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                span.set_attribute("gen_ai.error.type", type(exc).__name__)
                raise
            finally:
                latency_ms = (time.perf_counter() - start) * 1000
                span.set_attribute("gen_ai.latency_ms", round(latency_ms, 2))

    @contextmanager
    def tool_call(self, tool_name: str) -> Generator[Span, None, None]:
        """Context manager for a gen_ai.tool_call span."""
        attrs = self._base_attrs(**{"gen_ai.tool.name": tool_name})
        with self._tracer.start_as_current_span(
            "gen_ai.tool_call", attributes=attrs
        ) as span:
            yield span

    @contextmanager
    def retrieval(self, query: Optional[str] = None) -> Generator[Span, None, None]:
        """Context manager for a gen_ai.retrieval span."""
        attrs = self._base_attrs()
        if query:
            attrs["gen_ai.retrieval.query"] = query
        with self._tracer.start_as_current_span(
            "gen_ai.retrieval", attributes=attrs
        ) as span:
            yield span

    @contextmanager
    def guardrail(self, check_type: str) -> Generator[Span, None, None]:
        """Context manager for a gen_ai.guardrail span."""
        attrs = self._base_attrs(**{"gen_ai.guardrail.type": check_type})
        with self._tracer.start_as_current_span(
            "gen_ai.guardrail", attributes=attrs
        ) as span:
            yield span
