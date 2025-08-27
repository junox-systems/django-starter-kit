# OpenTelemetry Integration with SigNoz

This Django starter kit includes built-in OpenTelemetry support for distributed tracing and monitoring. The integration works with SigNoz and other OpenTelemetry-compatible backends.

## Prerequisites

1. Ensure you have the required OpenTelemetry packages installed (already included in pyproject.toml):
   - opentelemetry-sdk
   - opentelemetry-exporter-otlp
   - opentelemetry-instrumentation-django
   - opentelemetry-instrumentation-logging
   - opentelemetry-instrumentation-psycopg
   - opentelemetry-instrumentation-redis
   - opentelemetry-instrumentation-requests
   - opentelemetry-instrumentation-system-metrics
   - opentelemetry-instrumentation-urllib
   - opentelemetry-instrumentation-urllib3
   - opentelemetry-instrumentation-asyncio
   - opentelemetry-instrumentation-threading
   - opentelemetry-instrumentation-sqlite3

## Configuration

The OpenTelemetry integration is configured through environment variables in your `.env` file:

```env
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=django-starter-kit
OTEL_SERVICE_VERSION=1.0.0
```

## Using with SigNoz

For instructions on how to set up SigNoz with this Django application, please refer to the official SigNoz documentation:
[https://signoz.io/docs/install/self-host/](https://signoz.io/docs/install/self-host/)

## Using with other OpenTelemetry backends

To use with other OpenTelemetry-compatible backends like Jaeger, Zipkin, or New Relic:

1. Update the `OTEL_EXPORTER_OTLP_ENDPOINT` in your `.env` file to point to your backend
2. If your backend requires authentication, add the appropriate headers:
   ```env
   OTEL_EXPORTER_OTLP_HEADERS=authorization=Bearer your-token-here
   ```

## Instrumenting your code

The OpenTelemetry integration automatically instruments:
- Django HTTP requests and responses
- Database queries (PostgreSQL via psycopg3)
- Redis operations
- Outgoing HTTP requests
- System metrics (CPU, memory, disk usage)
- Async operations
- Threading operations

To add custom spans to your code:

```python
from opentelemetry import trace

# Get a tracer
tracer = trace.get_tracer(__name__)

# Create spans manually
with tracer.start_as_current_span("my-operation"):
    # Your code here
    pass
```

## Disabling OpenTelemetry

To disable OpenTelemetry, simply set `OTEL_ENABLED=false` in your `.env` file or remove the variable entirely.

## Troubleshooting

1. If you're not seeing traces in SigNoz, check that:
   - The SigNoz services are running
   - The `OTEL_EXPORTER_OTLP_ENDPOINT` points to the correct address
   - Your Django application is running with `OTEL_ENABLED=true`

2. If you're getting connection errors, ensure that:
   - The ports are correctly mapped in your Docker configuration
   - Your firewall isn't blocking the connections
   - The services are healthy

3. For debugging, you can enable debug logging by setting:
   ```env
   OTEL_LOG_LEVEL=DEBUG
```