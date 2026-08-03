# config/otel.py
import logging
import os

from typing import Optional

logger = logging.getLogger(__name__)


def initialize_opentelemetry() -> Optional[object]:
    """
    Initialize OpenTelemetry tracing and log export for the Django application.

    Called from apps/core/apps.py ready() hook. The SDK's built-in fork-awareness
    handles worker processes automatically via os.register_at_fork().

    Returns:
        TracerProvider: The initialized tracer provider or None if OTel is disabled.
    """
    otel_enabled = os.environ.get("OTEL_ENABLED", "").lower() in ("true", "1", "yes")

    if not otel_enabled:
        logger.info("OpenTelemetry not enabled, skipping initialization.")
        return None

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
            OTLPLogExporter,
        )
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

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

        otlp_endpoint = os.environ.get(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
        )

        # Traces
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        DjangoInstrumentor().instrument()
        PsycopgInstrumentor().instrument()
        RedisInstrumentor().instrument()

        # Logs — forward stdlib logging (WARNING and above) to the OTLP endpoint.
        log_provider = LoggerProvider(resource=resource)
        log_processor = BatchLogRecordProcessor(
            OTLPLogExporter(endpoint=otlp_endpoint, insecure=True)
        )
        log_provider.add_log_record_processor(log_processor)
        logging.getLogger().addHandler(
            LoggingHandler(level=logging.WARNING, logger_provider=log_provider)
        )

        logger.info(
            "OpenTelemetry initialized with endpoint: %s", otlp_endpoint
        )
        return provider

    except Exception:
        logger.exception("Failed to initialize OpenTelemetry")
        return None
