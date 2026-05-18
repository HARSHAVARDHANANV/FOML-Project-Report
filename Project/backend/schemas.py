"""
Request and response schemas with input validation.
Uses Pydantic v2 for automatic validation and documentation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class SegmentRequest(BaseModel):
    """Request body for customer segmentation endpoint."""

    Income: float = Field(..., ge=1, le=1000000, description="Customer annual income (1–1,000,000)")
    SpendingScore: float = Field(..., ge=1, le=100, description="Spending tendency score (1–100)")
    Frequency: float = Field(..., ge=0, le=365, description="Purchases per year (0–365)")
    Recency: float = Field(..., ge=0, le=3650, description="Days since last purchase (0–3650)")
    Monetary: float = Field(..., ge=0, le=1000000, description="Total amount spent (≥ 0)")

    @field_validator("Income")
    @classmethod
    def validate_income(cls, v):
        if v <= 0:
            raise ValueError("Income must be greater than 0")
        return v

    @field_validator("SpendingScore")
    @classmethod
    def validate_spending_score(cls, v):
        if not (1 <= v <= 100):
            raise ValueError("Spending Score must be between 1 and 100")
        return v

    @field_validator("Frequency")
    @classmethod
    def validate_frequency(cls, v):
        if not (0 <= v <= 365):
            raise ValueError("Frequency must be between 0 and 365")
        return v

    @field_validator("Recency")
    @classmethod
    def validate_recency(cls, v):
        if v < 0:
            raise ValueError("Recency cannot be negative")
        return v

    @field_validator("Monetary")
    @classmethod
    def validate_monetary(cls, v):
        if v < 0:
            raise ValueError("Monetary amount cannot be negative")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "Income": 50000,
                "SpendingScore": 75,
                "Frequency": 12,
                "Recency": 30,
                "Monetary": 5000,
            }
        }
    }


class SegmentResponse(BaseModel):
    """Response from segmentation endpoint."""
    cluster: int = Field(..., description="Assigned cluster ID (0-5)")
    segment: str = Field(..., description="Customer segment name")
    pattern: str = Field(..., description="Behavioral pattern for this segment")
    insight: str = Field(..., description="Actionable business insight")


class CustomerData(BaseModel):
    """Customer data with cluster assignment."""
    CustomerID: int
    Income: float
    SpendingScore: float
    Frequency: float
    Recency: float
    Monetary: float
    Cluster: int


class BatchCustomerRow(BaseModel):
    """A single customer row in a batch request (CustomerID optional)."""
    CustomerID: Optional[int] = None
    Income: float = Field(..., ge=1, le=1000000)
    SpendingScore: float = Field(..., ge=1, le=100)
    Frequency: float = Field(..., ge=0, le=365)
    Recency: float = Field(..., ge=0, le=3650)
    Monetary: float = Field(..., ge=0, le=1000000)


class BatchSegmentRequest(BaseModel):
    """
    JSON body for batch segmentation.
    Use min_length/max_length (Pydantic v2) — NOT min_items/max_items (v1).
    """
    customers: list[BatchCustomerRow] = Field(
        ...,
        min_length=1,    # Pydantic v2 — was min_items in v1
        max_length=1000, # Pydantic v2 — was max_items in v1
        description="List of customers to segment (1–1000)",
    )


class BatchSegmentResult(BaseModel):
    """Result for a single customer in a batch."""
    row_index: int
    CustomerID: Optional[int] = None
    Income: float
    SpendingScore: float
    Frequency: float
    Recency: float
    Monetary: float
    cluster: Optional[int] = None
    segment: Optional[str] = None
    pattern: Optional[str] = None
    insight: Optional[str] = None
    error: Optional[str] = None


class BatchSegmentResponse(BaseModel):
    """Response from batch segmentation endpoint."""
    total: int = Field(..., description="Total customers processed")
    successful: int = Field(..., description="Successfully segmented")
    failed: int = Field(..., description="Failed segmentations")
    results: list[BatchSegmentResult] = Field(..., description="Per-row segmentation results")


class ClusterStats(BaseModel):
    """Cluster statistics response."""
    cluster_id: int
    size: int
    avg_income: float
    avg_spending_score: float
    avg_frequency: float
    avg_recency: float
    avg_monetary: float
    segment_name: str


class ModelStats(BaseModel):
    """Overall model statistics."""
    total_customers: int
    clusters: list[ClusterStats]
    silhouette_score: Optional[float] = None
    inertia: Optional[float] = None