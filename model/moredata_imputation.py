import pandas as pd
import numpy as np
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge
import os

df = pd.read_excel(
    "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/MS_In_situ_Vannmiljo_lakes_coastals.xlsx"
)
df = df[df["s"] == "VT16"].copy()

df = df.rename(columns={
    "CDOM_insitu": "CDOM",
    "KLFA_insitu": "KLFA",
    "TSM_insitu": "TSM",
    "s": "Station",
    "Prøvetakingstidspunkt": "date"
})

df["date"] = pd.to_datetime(df["date"])

# Aggregate per day
vars_to_model = ["KLFA", "TSM", "SECCI", "CDOM"]
df_daily = df.groupby("date", as_index=False)[vars_to_model].mean()
df_daily["Station"] = "VT16"
df_daily["month"] = df_daily["date"].dt.month

print(df_daily)

# MICE IMPUTATION
imputer = IterativeImputer(
    estimator=BayesianRidge(),
    max_iter=50,
    random_state=42,
    sample_posterior=False
)

imputed_array = imputer.fit_transform(df_daily[vars_to_model])
df_imp = df_daily.copy()
df_imp[vars_to_model] = imputed_array

# Mark imputed cells
for col in vars_to_model:
    df_imp[col + "_imputed"] = df_daily[col].isna()

bounds = {
    "SECCI": (5, 25),
    "CDOM": (0.07, 0.56),
    "KLFA": (0.12, 5.1),
    "TSM": (0.097, 5.9)
}

for col, (lower, upper) in bounds.items():
    df_imp[col] = df_imp[col].clip(lower, upper)

# Save imputed data
output_path = "/Users/emma/Library/CloudStorage/OneDrive-DanmarksTekniskeUniversitet/Thesis/data/model/VT16_imputed_NO_synthetic.csv"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df_imp.to_csv(output_path, index=False)

print("DONE!")
print("Rows:", len(df_imp))
print(df_imp.head())
