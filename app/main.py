from fastapi import FastAPI
from app.core.config import settings
from app.routes import schools, students, invoices

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
)

# Include routers
app.include_router(schools.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(invoices.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/")
def root():
    return {"message": "School Billing API"}
