from pathlib import Path
import json
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import roc_auc_score, log_loss
from econml.dml import CausalForestDML

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "customers.csv"
REPORT_DIR = ROOT / "reports"
RESULT_FILE = REPORT_DIR / "customer_ite.csv"
METRICS_FILE = REPORT_DIR / "causal_metrics.json"


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def true_synthetic_effects(X):
    """Known effects from backend/generate_data.py."""
    baseline_logit = (
        -1.45
        + 1.15 * X["engagement"].to_numpy()
        + 0.12 * X["prior_purchases"].to_numpy()
        + 0.006 * (X["avg_order_value"].to_numpy() - 65)
        + 0.35 * X["loyalty_member"].to_numpy()
        - 0.004 * X["days_since_last_purchase"].to_numpy()
        - 0.003 * (X["age"].to_numpy() - 40)
    )

    sensitivity = (
        0.45
        + 0.95 * (1 - X["engagement"].to_numpy())
        + 0.18 * X["loyalty_member"].to_numpy()
    )

    p0 = sigmoid(baseline_logit)
    p10 = sigmoid(baseline_logit + sensitivity)
    p20 = sigmoid(baseline_logit + 2 * sensitivity)

    return p10 - p0, p20 - p0




FEATURES = [
    "age",
    "prior_purchases",
    "avg_order_value",
    "engagement",
    "days_since_last_purchase",
    "loyalty_member",
]


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "Dataset missing. Run python backend/generate_data.py"
        )

    df = pd.read_csv(DATA_FILE)

    X = df[FEATURES].copy()
    T = df["discount_amount"].astype(int)  # 0, 10, or 20
    Y = df["purchased"].astype(int)

    # Keep a held-out set for effect estimation and diagnostics.
    X_train, X_test, T_train, T_test, Y_train, Y_test, idx_train, idx_test = (
        train_test_split(
            X, T, Y, df.index,
            test_size=0.25,
            random_state=42,
            stratify=T,
        )
    )

    # Nuisance models estimate treatment assignment and purchase outcome.
    model_t = RandomForestClassifier(
        n_estimators=150,
        min_samples_leaf=20,
        random_state=42,
        n_jobs=-1,
    )
    model_y = RandomForestRegressor(
        n_estimators=150,
        min_samples_leaf=20,
        random_state=42,
        n_jobs=-1,
    )

    # Discrete treatment lets us compare $10 and $20 offers
    # against the no-discount baseline ($0).
    est = CausalForestDML(
        model_y=model_y,
        model_t=model_t,
        discrete_treatment=True,
        categories=[0, 10, 20],
        n_estimators=200,
        min_samples_leaf=20,
        max_depth=10,
        cv=3,
        random_state=42,
        n_jobs=-1,
    )

    est.fit(
        Y_train.to_numpy(),
        T_train.to_numpy(),
        X=X_train,
        inference="auto",
    )
    
# Predict purchase probabilities for each discount option.
    outcome_features_train = X_train.copy()
    outcome_features_train["discount_amount"] = T_train.to_numpy()

    outcome_probability_model = RandomForestClassifier(
    n_estimators=200,
    min_samples_leaf=20,
    random_state=42,
    n_jobs=-1,
    )

    outcome_probability_model.fit(outcome_features_train, Y_train)


    def predict_purchase_probability(discount):
     prediction_data = X_test.copy()
     prediction_data["discount_amount"] = discount

     class_index = list(
        outcome_probability_model.classes_
     ).index(1)

     return outcome_probability_model.predict_proba(
        prediction_data[outcome_features_train.columns]
    )[:, class_index]


    p0 = predict_purchase_probability(0)
    p10 = predict_purchase_probability(10)
    p20 = predict_purchase_probability(20)




    # Estimated change in purchase probability vs no discount.
    effect_10 = est.effect(
        X_test, T0=0, T1=10
    ).reshape(-1)
    effect_20 = est.effect(
        X_test, T0=0, T1=20
    ).reshape(-1)

    
# Predict baseline purchase probability.
    baseline_probability = est.model_y  # The fitted outcome model is stored in the estimator.

# Estimated treatment effects are probability differences.
# Clip the resulting probabilities to the valid [0, 1] range.
    p0 = np.clip(
    1 - effect_10 * 0 + 0, 0, 1
)

    
    true_10, true_20 = true_synthetic_effects(X_test)

    mae_10 = np.mean(np.abs(effect_10 - true_10))
    mae_20 = np.mean(np.abs(effect_20 - true_20))

    rmse_10 = np.sqrt(np.mean((effect_10 - true_10) ** 2))
    rmse_20 = np.sqrt(np.mean((effect_20 - true_20) ** 2))

    print(f"True-effect MAE ($10): {mae_10:.4f}")
    print(f"True-effect RMSE ($10): {rmse_10:.4f}")
    print(f"True-effect MAE ($20): {mae_20:.4f}")
    print(f"True-effect RMSE ($20): {rmse_20:.4f}")


    def evaluate_effect_accuracy(X_test, est_effect_10, est_effect_20):
        """Compare estimated effects to the known synthetic treatment effect."""
        true_10, true_20 = true_synthetic_effects(X_test)

        mae_10 = np.mean(np.abs(est_effect_10 - true_10))
        mae_20 = np.mean(np.abs(est_effect_20 - true_20))
        rmse_10 = np.sqrt(np.mean((est_effect_10 - true_10) ** 2))
        rmse_20 = np.sqrt(np.mean((est_effect_20 - true_20) ** 2))
        return mae_10, mae_20, rmse_10, rmse_20

    mae_10, mae_20, rmse_10, rmse_20 = evaluate_effect_accuracy(
        X_test, effect_10, effect_20
    )

    print(f"True-effect MAE ($10): {mae_10:.4f}")
    print(f"True-effect RMSE ($10): {rmse_10:.4f}")
    print(f"True-effect MAE ($20): {mae_20:.4f}")
    print(f"True-effect RMSE ($20): {rmse_20:.4f}")


    # Out-of-sample treatment assignment diagnostics.
    propensity_model = RandomForestClassifier(
        n_estimators=150,
        min_samples_leaf=20,
        random_state=42,
        n_jobs=-1,
    )
    propensity_model.fit(X_train, T_train)
    propensity = propensity_model.predict_proba(X_test)

    auc = roc_auc_score(
        T_test,
        propensity,
        multi_class="ovr",
        average="macro",
        labels=propensity_model.classes_,
    )
    test_log_loss = log_loss(
        T_test,
        propensity,
        labels=propensity_model.classes_,
    )

    
    
    results = df.loc[
    idx_test,
    [
        "customer_id",
        "discount_amount",
        "purchased",
        "avg_order_value",
    ],
].copy()

    results["ite_discount_10"] = effect_10
    results["ite_discount_20"] = effect_20

    results["purchase_probability_0"] = p0
    results["purchase_probability_10"] = p10
    results["purchase_probability_20"] = p20

    results["predicted_uplift_10_pp"] = effect_10 * 100
    results["predicted_uplift_20_pp"] = effect_20 * 100
    results["recommended_discount_by_uplift"] = np.select(
        [
            (effect_10 > 0) & (effect_10 >= effect_20),
            (effect_20 > 0) & (effect_20 > effect_10),
        ],
        [10, 20],
        default=0,
    )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(RESULT_FILE, index=False)

    metrics_payload = {
        "true_effect_mae_10": float(mae_10),
        "true_effect_mae_20": float(mae_20),
        "true_effect_rmse_10": float(rmse_10),
        "true_effect_rmse_20": float(rmse_20),
        "training_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "treatment_levels": [0, 10, 20],
        "treatment_propensity_macro_ovr_auc": float(auc),
        "treatment_propensity_log_loss": float(test_log_loss),
        "mean_estimated_uplift_10": float(np.mean(effect_10)),
        "mean_estimated_uplift_20": float(np.mean(effect_20)),
        "mean_estimated_uplift_10_percentage_points": float(
            np.mean(effect_10) * 100
        ),
        "mean_estimated_uplift_20_percentage_points": float(
            np.mean(effect_20) * 100
        ),
        "fraction_positive_effect_10": float(np.mean(effect_10 > 0)),
        "fraction_positive_effect_20": float(np.mean(effect_20 > 0)),
        "note": (
            "Propensity metrics measure treatment-assignment prediction, "
            "not causal-effect accuracy. Validate overlap and use the known "
            "synthetic mechanism for causal-effect evaluation."
        ),
    }
    METRICS_FILE.write_text(
        json.dumps(metrics_payload, indent=2),
        encoding="utf-8",
    )

    print("=" * 55)
    print("ECONOCAUSAL: DOUBLE MACHINE LEARNING")
    print("=" * 55)
    print(f"Training rows: {len(X_train)}")
    print(f"Held-out rows: {len(X_test)}")
    print(f"Treatment propensity macro OVR AUC: {auc:.3f}")
    print(f"Treatment propensity log loss: {test_log_loss:.3f}")
    print(f"Mean estimated uplift for $10: {np.mean(effect_10) * 100:.2f} pp")
    print(f"Mean estimated uplift for $20: {np.mean(effect_20) * 100:.2f} pp")
    print(f"\nSaved customer estimates: {RESULT_FILE}")
    print(f"Saved metrics: {METRICS_FILE}")






if __name__ == "__main__":
    main()
