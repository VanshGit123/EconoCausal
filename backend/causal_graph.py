from pathlib import Path
import pandas as pd
from dowhy import CausalModel

# Project paths
ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "customers.csv"
OUTPUT_DIR = ROOT / "reports"
GRAPH_FILE = OUTPUT_DIR / "causal_graph.dot"

df = pd.read_csv("data/customers.csv")

# Define the causal hypothesis using a DOT graph.
# Confounders point to both discount assignment and purchase.
graph = """
digraph {
    engagement -> discount_amount;
    engagement -> purchased;

    prior_purchases -> discount_amount;
    prior_purchases -> purchased;

    loyalty_member -> discount_amount;
    loyalty_member -> purchased;

    days_since_last_purchase -> discount_amount;
    days_since_last_purchase -> purchased;

    age -> purchased;
    avg_order_value -> purchased;

    discount_amount -> purchased;
}
"""

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GRAPH_FILE.write_text(graph, encoding="utf-8")

# Build the CausalModel before identifying the estimand.
model = CausalModel(
    data=df,
    treatment="discount_amount",
    outcome="purchased",
    graph=graph,
)

# Ask DoWhy to identify the causal estimand.
identified_estimand = model.identify_effect(
    proceed_when_unidentifiable=False
)

print("=" * 55)
print("ECONOCAUSAL: CAUSAL GRAPH ANALYSIS")
print("=" * 55)
print(f"Dataset rows: {len(df)}")
print(f"Treatment: discount_amount")
print(f"Outcome: purchased")
print("\nIdentified causal estimand:")
print(identified_estimand)

print("\nBackdoor adjustment variables:")
print(
    "engagement, prior_purchases, loyalty_member, "
    "days_since_last_purchase"
)

print(f"\nGraph saved to: {GRAPH_FILE}")
print("\nCausal graph identification completed.")
