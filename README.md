# EconoCausal — Step 1 Starter

This starter creates a synthetic observational marketing dataset for the EconoCausal project.

## Recommended environment
Use Python 3.11 for the full project because causal-ML package compatibility can vary by Python version.

## Setup (Windows PowerShell)
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
python backend/generate_data.py
```

If `py -3.11` is unavailable, install Python 3.11 first, then rerun the commands.

## Step 1 output
The script writes `data/customers.csv` with customer features, the assigned discount, and a binary purchase outcome. It also prints summary statistics.

## Important causal caveat
This is synthetic observational data. DML can adjust for measured confounders under assumptions such as adequate overlap and no unmeasured confounding; it cannot magically prove individual counterfactual outcomes.
