
from pathlib import Path

import json
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"

ITE_FILE = REPORT_DIR / "customer_ite.csv"
OPTIMIZED_FILE = REPORT_DIR / "optimized_discounts.csv"
SUMMARY_FILE = REPORT_DIR / "optimization_summary.json"
METRICS_FILE = REPORT_DIR / "causal_metrics.json"

app = FastAPI(
    title="EconoCausal API",
    description="Causal ML and profit-aware discount recommendations",
    version="1.0.0",
)

# For local development. Restrict this to your frontend origin in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def read_csv_report(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Report not found: {path.name}. Run the model pipeline first.",
        )
    try:
        return pd.read_csv(path)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read {path.name}: {exc}",
        )


def read_json_report(path: Path) -> dict:
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Report not found: {path.name}. Run the model pipeline first.",
        )
    try:
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read {path.name}: {exc}",
        )


@app.get("/")
def home():
    return {
        "project": "EconoCausal",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/metrics")
def get_metrics():
    return {
        "causal_metrics": read_json_report(METRICS_FILE),
        "optimization_summary": read_json_report(SUMMARY_FILE),
    }


@app.get("/api/customers")
def get_customers(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    discount: int | None = Query(default=None, description="Filter by recommended discount: 0, 10, or 20"),
):
    df = read_csv_report(OPTIMIZED_FILE)

    if discount is not None:
        if discount not in [0, 10, 20]:
            raise HTTPException(
                status_code=400,
                detail="discount must be 0, 10, or 20",
            )
        df = df[df["recommended_discount"] == discount]

    total = len(df)
    page = df.iloc[offset:offset + limit]

    # Convert NaN and NumPy values into JSON-safe Python values.
    records = json.loads(page.to_json(orient="records"))

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "customers": records,
    }


@app.get("/api/customers/{customer_id}")
def get_customer(customer_id: str):
    df = read_csv_report(OPTIMIZED_FILE)

    matches = df[
        df["customer_id"].astype(str) == str(customer_id)
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail="Customer not found in the optimization report.",
        )

    return json.loads(matches.iloc[0:1].to_json(orient="records"))[0]


@app.get("/api/discount-distribution")
def discount_distribution():
    df = read_csv_report(OPTIMIZED_FILE)

    if "recommended_discount" not in df.columns:
        raise HTTPException(
            status_code=500,
            detail="recommended_discount column is missing.",
        )

    counts = df["recommended_discount"].value_counts()

    return {
        "distribution": [
            {"discount": discount, "customers": int(counts.get(discount, 0))}
            for discount in [0, 10, 20]
        ]
    }
