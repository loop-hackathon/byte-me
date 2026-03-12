"""
Distributed Tracing configuration for CloudHelm backend.

This module sets up OpenTelemetry tracing and exports traces to the
OpenTelemetry Collector via OTLP HTTP protocol.

Pipeline: backend → OTLP Collector (port 4318) → Grafana Tempo → Grafana
"""
import os
import logging

logger = logging.getLogger(__name__)

# The OTLP endpoint for the OpenTelemetry Collector.
# In development this points to localhost; in Docker it uses the service name.
OTEL_EXPORTER_ENDPOINT = os.getenv(
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "http://localhost:4318/v1/traces"
)


def setup_tracing(sqlalchemy_engine=None) -> None:
    """
    Initialise the OpenTelemetry TracerProvider for the backend.

    Call this ONCE at application startup before any requests are received.

    Args:
        sqlalchemy_engine: The SQLAlchemy engine instance to instrument.
            When provided, every SQL query will appear as a child span
            inside the currently active trace.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        # ── 1. Define the service resource ──────────────────────────────────
        resource = Resource.create({SERVICE_NAME: "cloudhelm-backend"})

        # ── 2. Create the tracer provider ───────────────────────────────────
        provider = TracerProvider(resource=resource)

        # ── 3. Configure the OTLP exporter ──────────────────────────────────
        try:
            exporter = OTLPSpanExporter(endpoint=OTEL_EXPORTER_ENDPOINT)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(
                "OpenTelemetry tracing enabled → exporting to: %s",
                OTEL_EXPORTER_ENDPOINT
            )
        except Exception as exc:
            logger.warning(
                "Could not configure OTLP exporter (%s). "
                "Traces will not be exported but the application will continue normally.",
                exc
            )

        # ── 4. Register the provider globally ───────────────────────────────
        trace.set_tracer_provider(provider)

        # ── 5. Instrument SQLAlchemy ─────────────────────────────────────────
        if sqlalchemy_engine is not None:
            try:
                from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
                SQLAlchemyInstrumentor().instrument(engine=sqlalchemy_engine)
                logger.info("SQLAlchemy instrumented — database queries will appear as spans.")
            except ImportError:
                logger.warning("opentelemetry-instrumentation-sqlalchemy not installed. Skipping DB instrumentation.")

    except ImportError:
        logger.warning(
            "OpenTelemetry packages not installed. "
            "Tracing will be disabled but the application will continue normally. "
            "Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http"
        )


def get_tracer(name: str = "cloudhelm"):
    """
    Convenience helper to obtain a named tracer.

    Usage in any service file:
        from backend.core.tracing import get_tracer
        tracer = get_tracer(__name__)

        with tracer.start_as_current_span("my-operation") as span:
            span.set_attribute("key", "value")
            # your logic here
    """
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return None
