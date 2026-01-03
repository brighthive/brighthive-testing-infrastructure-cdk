"""OpenTelemetry distributed tracing configuration.

Provides distributed tracing for request tracking across services.
"""

import os
from typing import Any, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor



def setup_tracing(
    service_name: str = "brighthive_testing_cdk",
    otlp_endpoint: Optional[str] = None,
) -> None:
    """Configure OpenTelemetry tracing.

    Args:
        service_name: Name of the service for tracing
        otlp_endpoint: OTLP collector endpoint (defaults to env var OTEL_EXPORTER_OTLP_ENDPOINT)

    Example:
        >>> from brighthive_testing_cdk.tracing import setup_tracing
        >>> setup_tracing(service_name="my-service")
    """
    endpoint = otlp_endpoint or os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://localhost:4317",
    )

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "0.1.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        }
    )

    tracer_provider = TracerProvider(resource=resource)

    otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    trace.set_tracer_provider(tracer_provider)


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance.

    Args:
        name: Tracer name (typically module name)

    Returns:
        Tracer: OpenTelemetry tracer instance

    Example:
        >>> from brighthive_testing_cdk.tracing import get_tracer
        >>> tracer = get_tracer(__name__)
        >>> with tracer.start_as_current_span("operation"):
        ...     # Your code here
        ...     pass
    """
    return trace.get_tracer(name)





__all__ = [
    "setup_tracing",
    "get_tracer",
    
]

