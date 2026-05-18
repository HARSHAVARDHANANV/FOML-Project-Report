"""
FastAPI application for customer segmentation.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List
import pandas as pd
import io
import os
from model import model, init_model
from config import get_settings
from schemas import (
    SegmentRequest, SegmentResponse, CustomerData,
    BatchSegmentRequest, BatchSegmentResponse, BatchSegmentResult,
)

settings = get_settings()


# ── Lifespan (replaces deprecated @app.on_event("startup")) ──────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize ML model before the app starts accepting requests."""
    possible_paths = [
        settings.DATASET_PATH,
        "../Customers_dataset.csv",
        "../../Customers_dataset.csv",
        "Customers_dataset.csv",
        "./Customers_dataset.csv",
    ]
    found = False
    for path in possible_paths:
        if os.path.exists(path):
            try:
                init_model(path)
                print(f"✓ Model initialized with data from {path}")
                found = True
                break
            except Exception as e:
                print(f"Error initializing model from {path}: {e}")

    if not found:
        print("⚠ Warning: Could not initialize model - dataset not found")

    yield  # app runs here


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="ML-based customer segmentation API using K-Means clustering",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
# NOTE: TrustedHostMiddleware removed — it blocked all non-localhost requests,
# breaking any deployed or Docker environment. CORS below handles origin control.

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
#"GET", "POST"
#"Content-Type"
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ── Helpers ───────────────────────────────────────────────────────────────────
def _find_dataset() -> str | None:
    for path in [
        settings.DATASET_PATH,
        "../Customers_dataset.csv",
        "../../Customers_dataset.csv",
        "Customers_dataset.csv",
        "./Customers_dataset.csv",
    ]:
        if os.path.exists(path):
            return path
    return None


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/segment", response_model=SegmentResponse)
async def segment_customer(request: SegmentRequest):
    """Segment a single customer based on their features."""
    result = model.predict(
        income=request.Income,
        spending_score=request.SpendingScore,
        frequency=request.Frequency,
        recency=request.Recency,
        monetary=request.Monetary,
    )
    return SegmentResponse(**result)


@app.post("/batch", response_model=BatchSegmentResponse)
async def batch_segment(file: UploadFile = File(...)):
    """
    Accept a CSV upload and segment every row.

    Expected CSV columns (case-sensitive):
        CustomerID (optional), Income, SpendingScore, Frequency, Recency, Monetary
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    required = {"Income", "SpendingScore", "Frequency", "Recency", "Monetary"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"CSV is missing required columns: {missing}",
        )

    results: list[BatchSegmentResult] = []
    successful = 0
    failed = 0

    for idx, row in df.iterrows():
        customer_id = int(row["CustomerID"]) if "CustomerID" in df.columns and pd.notna(row.get("CustomerID")) else None
        base = dict(
            row_index=int(idx),
            CustomerID=customer_id,
            Income=row["Income"],
            SpendingScore=row["SpendingScore"],
            Frequency=row["Frequency"],
            Recency=row["Recency"],
            Monetary=row["Monetary"],
        )
        try:
            prediction = model.predict(
                income=float(row["Income"]),
                spending_score=float(row["SpendingScore"]),
                frequency=float(row["Frequency"]),
                recency=float(row["Recency"]),
                monetary=float(row["Monetary"]),
            )
            results.append(BatchSegmentResult(**base, **prediction))
            successful += 1
        except Exception as e:
            results.append(BatchSegmentResult(**base, error=str(e)))
            failed += 1

    return BatchSegmentResponse(
        total=len(results),
        successful=successful,
        failed=failed,
        results=results,
    )


@app.get("/export")
async def export_customers():
    """Download all customer data with cluster assignments as a CSV file."""
    data_path = _find_dataset()
    if not data_path:
        raise HTTPException(status_code=404, detail="Customer dataset not found.")

    df = pd.read_csv(data_path)
    result_df = model.get_all_customers_with_clusters(df)

    stream = io.StringIO()
    result_df.to_csv(stream, index=False)
    stream.seek(0)

    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=customer_segments.csv"},
    )


@app.get("/data", response_model=List[CustomerData])
async def get_customer_data():
    """Get all customer data with cluster assignments for visualization."""
    data_path = _find_dataset()
    if not data_path:
        return []

    df = pd.read_csv(data_path)
    result_df = model.get_all_customers_with_clusters(df)
    return result_df.to_dict("records")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=(settings.SERVER_ENVIRONMENT == "development"),
    )