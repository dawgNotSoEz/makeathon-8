from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest


REQUEST_COUNT = Counter(
    "backend_http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status_code"],
)

REQUEST_DURATION = Histogram(
    "backend_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.01, 0.03, 0.05, 0.1, 0.2, 0.5, 1, 2, 5),
)

LLM_OPERATION_DURATION = Histogram(
    "backend_llm_operation_duration_seconds",
    "LLM operation latency in seconds",
    ["operation"],
    buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 40),
)

LLM_OPERATION_FAILURES = Counter(
    "backend_llm_operation_failures_total",
    "Total number of LLM operation failures",
    ["operation"],
)

VECTOR_QUERY_DURATION = Histogram(
    "backend_vector_query_duration_seconds",
    "Vector store query latency in seconds",
    ["operation"],
    buckets=(0.005, 0.01, 0.03, 0.05, 0.1, 0.2, 0.5, 1, 2),
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
