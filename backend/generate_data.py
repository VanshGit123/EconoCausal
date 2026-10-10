from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
N_CUSTOMERS = 8000
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_FILE = DATA_DIR / "customers.csv"


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def make_dataset(n=N_CUSTOMERS, seed=SEED):
    rng = np.random.default_rng(seed)

    # Customer features available before the campaign.
    age = rng.integers(18, 71, size=n)
    prior_purchases = rng.poisson(3.0, size=n)
    avg_order_value = np.clip(rng.normal(65, 22, size=n), 10, 180)
    engagement = rng.beta(2.2, 2.0, size=n)  # 0 to 1
    days_since_last_purchase = np.clip(
        rng.exponential(35, size=n), 0, 180
    ).round().astype(int)
    loyalty_member = rng.binomial(1, 0.38, size=n)

    # Observational treatment assignment:
    # highly engaged / loyal customers have different odds of receiving offers.
    treatment_logit = (
        -1.0
        + 1.25 * engagement
        + 0.20 * loyalty_member
        + 0.06 * prior_purchases
        - 0.008 * days_since_last_purchase
    )
    treatment_probability = sigmoid(treatment_logit)
    gets_discount = rng.binomial(1, treatment_probability, size=n)

    # Offered discount among treated customers: $10 or $20.
    # Assignment depends on observed customer characteristics too.
    high_discount_logit = (
        -0.65 + 0.8 * (1 - engagement) + 0.025 * days_since_last_purchase
    )
    high_discount_probability = sigmoid(high_discount_logit)
    is_20_offer = rng.binomial(1, high_discount_probability, size=n)
    discount_amount = np.where(
        gets_discount == 1, np.where(is_20_offer == 1, 20.0, 10.0), 0.0
    )

    # True purchase response. The discount effect varies across customers:
    # lower-engagement customers tend to be more persuadable.
    baseline_logit = (
        -1.45
        + 1.15 * engagement
        + 0.12 * prior_purchases
        + 0.006 * (avg_order_value - 65)
        + 0.35 * loyalty_member
        - 0.004 * days_since_last_purchase
        - 0.003 * (age - 40)
    )
    individual_sensitivity = 0.45 + 0.95 * (1 - engagement) + 0.18 * loyalty_member
    discount_effect = individual_sensitivity * (discount_amount / 10.0)
    purchase_probability = sigmoid(baseline_logit + discount_effect)
    purchased = rng.binomial(1, purchase_probability, size=n)

    df = pd.DataFrame({
        "customer_id": [f"C{i:05d}" for i in range(1, n + 1)],
        "age": age,
        "prior_purchases": prior_purchases,
        "avg_order_value": avg_order_value.round(2),
        "engagement": engagement.round(4),
        "days_since_last_purchase": days_since_last_purchase,
        "loyalty_member": loyalty_member,
        "treatment_probability": treatment_probability.round(4),
        "discount_amount": discount_amount,
        "purchased": purchased,
    })
    return df


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = make_dataset()
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved {len(df):,} customers to: {OUTPUT_FILE}")
    print("\nFirst five rows:")
    print(df.head().to_string(index=False))
    print("\nPurchase rate by discount:")
    print(
        df.groupby("discount_amount")["purchased"]
        .agg(customers="size", purchase_rate="mean")
        .round(3)
        .to_string()
    )
    print("\nMissing values by column:")
    print(df.isna().sum().to_string())


if __name__ == "__main__":
    main()
