from pathlib import Path
import pandas as pd
import sys

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "customers.csv"

REQUIRED_COLUMNS = [
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


def validate_dataset():
    if not DATA_PATH.exists():
        print(f"ERROR: Dataset not found: {DATA_PATH}")
        return False

    df = pd.read_csv(DATA_PATH)
    errors = []

    missing_columns = [
        col for col in REQUIRED_COLUMNS if col not in df.columns
    ]

    if missing_columns:
        errors.append(f"Missing columns: {missing_columns}")

    if missing_columns:
        print("\n".join(errors))
        return False

    if df.empty:
        errors.append("Dataset is empty.")

    if df["customer_id"].duplicated().any():
        errors.append("Duplicate customer IDs found.")

    if df[REQUIRED_COLUMNS].isnull().any().any():
        errors.append("Missing values found in required columns.")

    if (df["age"] < 0).any():
        errors.append("Age cannot be negative.")

    if (df["avg_order_value"] < 0).any():
        errors.append("Average order value cannot be negative.")

    if not df["treatment_probability"].between(0, 1).all():
        errors.append("Treatment probability must be between 0 and 1.")

    if not df["purchased"].isin([0, 1]).all():
        errors.append("Purchased must contain only 0 or 1.")

    if (df["discount_amount"] < 0).any():
        errors.append("Discount amount cannot be negative.")

    if errors:
        print("\nDATA VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return False

    print("DATA VALIDATION PASSED")
    print(f"Total customers: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print("No missing values or duplicate customer IDs found.")
    return True


if __name__ == "__main__":
    success = validate_dataset()
    sys.exit(0 if success else 1)