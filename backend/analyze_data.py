
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "customers.csv"
REPORT_DIR = ROOT / "reports"
REPORT_FILE = REPORT_DIR / "data_summary.json"


def main():
    df = pd.read_csv("data/customers.csv")

    required = [
        "customer_id",
        "age",
        "prior_purchases",
        "avg_order_value",
        "engagement",
        "days_since_last_purchase",
        "loyalty_member",
        "treatment_probability",
        "discount_amount",
        "purchased",
    ]

    missing_columns = [col for col in required if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    if df["customer_id"].duplicated().any():
        raise ValueError("Duplicate customer IDs found.")

    if df[required].isna().any().any():
        raise ValueError("Missing values found in required columns.")

    if not df["discount_amount"].isin([0, 10, 20]).all():
        raise ValueError("Unexpected discount amount.")

    if not df["purchased"].isin([0, 1]).all():
        raise ValueError("Purchase outcome must be 0 or 1.")

    summary = (
        df.groupby("discount_amount")
        .agg(
            customers=("customer_id", "count"),
            purchase_rate=("purchased", "mean"),
            avg_engagement=("engagement", "mean"),
            avg_prior_purchases=("prior_purchases", "mean"),
        )
        .reset_index()
    )

    summary["purchase_rate"] = summary["purchase_rate"].round(4)
    summary["avg_engagement"] = summary["avg_engagement"].round(4)
    summary["avg_prior_purchases"] = summary["avg_prior_purchases"].round(2)

    report = {
        "total_customers": int(len(df)),
        "total_columns": int(len(df.columns)),
        "overall_purchase_rate": round(float(df["purchased"].mean()), 4),
        "missing_values": {col: int(count) for col, count in df.isna().sum().items()},
        "discount_summary": summary.to_dict(orient="records"),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("DATA VALIDATION SUCCESSFUL")
    print("-" * 40)
    print("Customers:", len(df))
    print("Columns:", len(df.columns))
    print("Missing values:", int(df.isna().sum().sum()))
    print("Duplicate IDs:", df["customer_id"].duplicated().sum())

    print("\nPurchase statistics by discount:")
    print(summary.to_string(index=False))

    print(f"\nReport saved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()

