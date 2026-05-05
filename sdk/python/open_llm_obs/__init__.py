# open_llm_obs - Open LLM Observability SDK
# Apache 2.0 License

"""open_llm_obs: A vendor-neutral, OpenTelemetry-compatible SDK for LLM observability.

Usage:
    from open_llm_obs import instrument
    instrument(provider="openai", export_to="otlp")
"""

__version__ = "0.1.0"
__author__ = "sauravGit"
__license__ = "Apache-2.0"

from open_llm_obs.instrument import instrument
from open_llm_obs.metrics import LLMMetrics
from open_llm_obs.tracer import LLMTracer

__all__ = [
    "instrument",
    "LLMMetrics",
    "LLMTracer",
]
