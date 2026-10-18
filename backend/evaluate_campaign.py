
from pathlib import Path
import json
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULT_FILE = ROOT / "reports" / "customer_ite.csv"
OUTPUT_FILE = ROOT / "reports" / "campaign_evaluation.json"


def main():
    if not RESULT_FILE.exists():
        raise FileNotFoundError(
            "Run python backend/causal_model.py first."
        )

    df = pd.read_csv(RESULT_FILE)

    required = [
        "ite_discount_10",
        "ite_discount_20",
        "recommended_discount_by_uplift",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    recommendations = df["recommended_discount_by_uplift"]
    effect_10 = df["ite_discount_10"]
    effect_20 = df["ite_discount_20"]

    report = {
        "customers_evaluated": int(len(df)),
        "recommended_no_discount": int((recommendations == 0).sum()),
        "recommended_discount_10": int((recommendations == 10).sum()),
        "recommended_discount_20": int((recommendations == 20).sum()),
        "mean_predicted_uplift_10_pp": round(
            float(effect_10.mean() * 100), 3
        ),
        "mean_predicted_uplift_20_pp": round(
            float(effect_20.mean() * 100), 3
        ),
        "fraction_positive_uplift_10": round(
            float((effect_10 > 0).mean()), 4
        ),
        "fraction_positive_uplift_20": round(
            float((effect_20 > 0).mean()), 4
        ),
        "warning": (
            "These are model-based predictions, not proof of realized "
            "campaign impact. Validate with a randomized experiment."
        ),
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nSaved campaign evaluation: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
