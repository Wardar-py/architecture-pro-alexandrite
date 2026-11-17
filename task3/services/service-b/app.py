import os
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Настройка трейсинга (аналогично service-a)
trace.set_tracer_provider(TracerProvider())
tracer_provider = trace.get_tracer_provider()
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://simplest-collector:4318/v1/traces")
)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)
app = FastAPI()

FastAPIInstrumentor.instrument_app(app)



@app.get("/data")
def get_data():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("service-b-handler"):
        return {"data": "some valuable information"}