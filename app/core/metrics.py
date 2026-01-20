from prometheus_client import Counter, Histogram

# HTTP request metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

# Statement-specific metrics
SCHOOL_STATEMENT_REQUESTS_TOTAL = Counter(
    "school_statement_requests_total",
    "Total school statement requests",
    ["include_invoices"],
)

SCHOOL_STATEMENT_DURATION_SECONDS = Histogram(
    "school_statement_duration_seconds",
    "School statement generation duration",
)

STUDENT_STATEMENT_REQUESTS_TOTAL = Counter(
    "student_statement_requests_total",
    "Total student statement requests",
    ["include_invoices"],
)

STUDENT_STATEMENT_DURATION_SECONDS = Histogram(
    "student_statement_duration_seconds",
    "Student statement generation duration",
)
