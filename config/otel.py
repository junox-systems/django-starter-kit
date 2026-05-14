# config/otel.py
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def initialize_opentelemetry() -> Optional[object]:
    """
    Initialize OpenTelemetry tracing for the Django application.

    Returns:
        TracerProvider: The initialized tracer provider or None if OTel is disabled.
    """
    otel_enabled = os.environ.get("OTEL_ENABLED", "").lower() in ("true", "1", "yes")

    if not otel_enabled:
        logger.info("OpenTelemetry not enabled, skipping initialization.")
        return None

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        resource = Resource.create(
            {
                "service.name": os.environ.get(
                    "OTEL_SERVICE_NAME", "django-starter-kit"
                ),
                "service.version": os.environ.get("OTEL_SERVICE_VERSION", "1.0.0"),
                "deployment.environment": os.environ.get(
                    "ENVIRONMENT", "development"
                ),
            }
        )

        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        otlp_endpoint = os.environ.get(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://0.0.0.0:4317"
        )
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        DjangoInstrumentor().instrument()
        PsycopgInstrumentor().instrument()
        RedisInstrumentor().instrument()

        logger.info("OpenTelemetry initialized with endpoint: %s", otlp_endpoint)
        return provider

    except Exception:
        logger.exception("Failed to initialize OpenTelemetry")
        return None
