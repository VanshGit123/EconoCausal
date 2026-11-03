import pandas as pd
from backend import validate_data


def sample_dataset():
    return pd.DataFrame({
        "customer_id": [1, 2, 3],
        "age": [22, 25, 30],
        "prior_purchases": [2, 4, 5],
        "avg_order_value": [500, 700, 900],
        "engagement": [0.5, 0.7, 0.8],
        "days_since_last_purchase": [10, 20, 5],
        "loyalty_member": [1, 0, 1],
        "treatment_probability": [0.3, 0.5, 0.7],
        "discount_amount": [0, 10, 20],
        "purchased": [0, 1, 1]
    })


def test_valid_dataset(monkeypatch, tmp_path):
    file_path = tmp_path / "customers.csv"
    sample_dataset().to_csv(file_path, index=False)

    monkeypatch.setattr(validate_data, "DATA_PATH", file_path)

    assert validate_data.validate_dataset() is True


def test_duplicate_customer_ids(monkeypatch, tmp_path):
    file_path = tmp_path / "customers.csv"

    df = sample_dataset()
    df.loc[1, "customer_id"] = 1
    df.to_csv(file_path, index=False)

    monkeypatch.setattr(validate_data, "DATA_PATH", file_path)

    assert validate_data.validate_dataset() is False


def test_missing_values(monkeypatch, tmp_path):
    file_path = tmp_path / "customers.csv"

    df = sample_dataset()
    df.loc[0, "age"] = None
    df.to_csv(file_path, index=False)

    monkeypatch.setattr(validate_data, "DATA_PATH", file_path)

    assert validate_data.validate_dataset() is False