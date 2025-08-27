# config/otel.py
import os
from typing import Optional
import logging


def initialize_opentelemetry() -> Optional[object]:
    """
    Initialize OpenTelemetry tracing for the Django application.

    Returns:
        TracerProvider: The initialized tracer provider or None if OTel is disabled.
    """

    otel_enabled = os.environ.get("OTEL_ENABLED", False)

    if not otel_enabled:
        print("OpenTelemetry not enabled, skipping initialization.")
        logging.info("OpenTelemetry not enabled, skipping initialization.")
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
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        from opentelemetry.instrumentation.system_metrics import (
            SystemMetricsInstrumentor,
        )
        from opentelemetry.instrumentation.threading import ThreadingInstrumentor
        from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
        from opentelemetry.instrumentation.urllib import URLLibInstrumentor
        from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor

        # Create a resource with service information
        resource = Resource.create(
            {
                "service.name": os.environ.get(
                    "OTEL_SERVICE_NAME", "django-starter-kit"
                ),
                "service.version": os.environ.get("OTEL_SERVICE_VERSION", "1.0.0"),
                "deployment.environment": os.environ.get("ENVIRONMENT", "development"),
            }
        )

        # Create and set the tracer provider
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        # Configure OTLP exporter
        otlp_endpoint = os.environ.get(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://0.0.0.0:4317"
        )

        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=True,  # Set to False if using TLS
        )

        # Add batch span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)

        # Instrument Django - Traces HTTP requests and responses in Django applications
        DjangoInstrumentor().instrument()

        # Instrument database connections (psycopg3) - Traces database queries made with psycopg3
        PsycopgInstrumentor().instrument()

        # Instrument Redis - Traces Redis operations for caching and session storage
        RedisInstrumentor().instrument()

        # Instrument outgoing HTTP requests - Traces HTTP requests made with the requests library
        RequestsInstrumentor().instrument()

        # Instrument logging - Correlates log messages with traces for better debugging
        LoggingInstrumentor().instrument()

        # Instrument system metrics - Collects system-level metrics like CPU, memory, and disk usage
        SystemMetricsInstrumentor().instrument()

        # Instrument threading - Traces operations across threads for concurrent execution tracking
        ThreadingInstrumentor().instrument()

        # Instrument asyncio - Traces asynchronous operations for async/await code execution
        AsyncioInstrumentor().instrument()

        # Instrument urllib - Traces HTTP requests made with the standard library urllib
        URLLibInstrumentor().instrument()

        # Instrument urllib3 - Traces HTTP requests made with the urllib3 library
        URLLib3Instrumentor().instrument()

        print(f"OpenTelemetry initialized with endpoint: {otlp_endpoint}")
        return provider

    except Exception as e:
        print(f"Failed to initialize OpenTelemetry: {e}")
        return None
