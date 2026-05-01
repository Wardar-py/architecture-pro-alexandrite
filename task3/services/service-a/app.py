import os
from fastapi import FastAPI
import requests
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Настройка трейсинга
trace.set_tracer_provider(TracerProvider())
tracer_provider = trace.get_tracer_provider()

# Экспорт трейсов в Jaeger (через OTLP HTTP)
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://simplest-collector:4318/v1/traces")
)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)

app = FastAPI()


# Инструментация библиотек
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()



SERVICE_B_URL = os.getenv("SERVICE_B_URL", "http://service-b:8080")

@app.get("/")
def read_root():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("service-a-handler"):
        # Вызов Service B
        with tracer.start_as_current_span("call-service-b") as span:
            span.set_attribute("http.method", "GET")
            span.set_attribute("http.url", f"{SERVICE_B_URL}/data")
            try:
                response = requests.get(f"{SERVICE_B_URL}/data", timeout=5)
                data = response.json()
                return {"message": "Hello from service-a", "service_b_response": data}
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR)
                return {"error": str(e)}