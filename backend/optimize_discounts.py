
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "customers.csv"
ITE_FILE = ROOT / "reports" / "customer_ite.csv"
OUTPUT_FILE = ROOT / "reports" / "optimized_discounts.csv"
SUMMARY_FILE = ROOT / "reports" / "optimization_summary.json"

PROFIT_MARGIN = 0.30
DISCOUNT_OPTIONS = [0, 10, 20]


def main():
    customers = pd.read_csv(DATA_FILE)
    estimates = pd.read_csv(ITE_FILE)

    required = [
        "customer_id",
        "avg_order_value",
        "purchase_probability_0",
        "purchase_probability_10",
        "purchase_probability_20",
    ]

    missing = [c for c in required if c not in estimates.columns]
    if missing:
        raise ValueError(
            f"Missing columns in {ITE_FILE.name}: {missing}. "
            "Run the updated causal_model.py first."
        )

   
# Take order value from the original dataset.
    customer_values = customers[["customer_id", "avg_order_value"]].copy()

# Take the predicted purchase probabilities from the model report.
    required_estimates = [
    "customer_id",
    "purchase_probability_0",
    "purchase_probability_10",
    "purchase_probability_20",
    ]

    df = customer_values.merge(
    estimates[required_estimates],
    on="customer_id",
    how="inner",
    validate="one_to_one",
)

    if "avg_order_value" not in df.columns:
     raise ValueError("avg_order_value is missing after merging.")

    if df.empty:
     raise ValueError("No matching customer IDs found.")


    if df.empty:
        raise ValueError("No matching customer IDs found.")

    # Simplified expected profit per customer under each offer.
    for discount in DISCOUNT_OPTIONS:
        probability_column = f"purchase_probability_{discount}"
        df[f"expected_profit_{discount}"] = (
            df[probability_column]
            * (df["avg_order_value"] * PROFIT_MARGIN - discount)
        )

    profit_columns = {
        0: "expected_profit_0",
        10: "expected_profit_10",
        20: "expected_profit_20",
    }

    profit_matrix = np.column_stack(
        [df[profit_columns[d]].to_numpy() for d in DISCOUNT_OPTIONS]
    )

    best_indices = np.argmax(profit_matrix, axis=1)
    df["recommended_discount"] = np.array(DISCOUNT_OPTIONS)[best_indices]
    df["expected_profit_best"] = profit_matrix[
        np.arange(len(df)), best_indices
    ]

    # Baseline comparison is against offering no discount to everyone.
    df["expected_profit_no_discount"] = df["expected_profit_0"]
    df["incremental_expected_profit"] = (
        df["expected_profit_best"] - df["expected_profit_no_discount"]
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    summary = {
        "customers_evaluated": int(len(df)),
        "profit_margin_assumption": PROFIT_MARGIN,
        "recommended_discount_counts": {
            str(d): int((df["recommended_discount"] == d).sum())
            for d in DISCOUNT_OPTIONS
        },
        "total_expected_profit_if_no_discount": float(
            df["expected_profit_no_discount"].sum()
        ),
        "total_expected_profit_under_recommendations": float(
            df["expected_profit_best"].sum()
        ),
        "estimated_incremental_expected_profit": float(
            df["incremental_expected_profit"].sum()
        ),
        "warning": (
            "Model-based estimates, not guaranteed realized profit. "
            "Validate with a randomized campaign and actual margin data."
        ),
    }

    SUMMARY_FILE.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))
    print(f"\nSaved customer recommendations: {OUTPUT_FILE}")
    print(f"Saved summary: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
